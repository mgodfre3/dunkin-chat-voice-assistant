import logging
import os
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2
from aiohttp import web
from azure.core.credentials import AzureKeyCredential
from azure.identity import AzureDeveloperCliCredential, DefaultAzureCredential
from dotenv import load_dotenv

from crm import CRMRepository
from dashboard import dashboard_socket, reset_lane, spawn_car, complete_car, demo_status, start_demo_mode, stop_demo_mode
from drive_thru import (
    DriveThruSimulator,
    DriveThruDemoFleet,
    InMemorySimulatorStateStore,
    PostgresSimulatorStateStore,
    RedisSimulatorStateStore,
)
from rtmt import RTMiddleTier
from rtmt_local import RTLocalPipeline
from tools import attach_tools_rtmt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_bool_env(variable_name: str, default: bool = False) -> bool:
    """Parse boolean environment variables with predictable defaults."""
    value = os.environ.get(variable_name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


async def create_app() -> web.Application:
    """Configure and return the aiohttp application for realtime ordering."""

    if not _get_bool_env("RUNNING_IN_PRODUCTION", False):
        logger.info("Running in development mode; loading values from .env")
        load_dotenv()

    use_local = _get_bool_env("USE_LOCAL_PIPELINE", True)

    app = web.Application()

    crm_db_path = os.environ.get("CRM_DB_PATH")
    crm_repo = CRMRepository.from_env(crm_db_path)
    app["crm_repo"] = crm_repo

    simulator = await _create_simulator_from_env()
    app["drive_thru_simulator"] = simulator

    demo_fleet = DriveThruDemoFleet(simulator, crm_repo=crm_repo)
    app["drive_thru_demo"] = demo_fleet

    if _get_bool_env("DRIVE_THRU_DEMO_AUTOSTART", True):
        await demo_fleet.start()

    async def _stop_simulator(_app: web.Application) -> None:
        await demo_fleet.stop()
        await simulator.stop()

    app.on_cleanup.append(_stop_simulator)

    if use_local:
        logger.info("Using LOCAL pipeline (Whisper STT → Phi-4 Mini → Piper TTS)")
        rtmt = RTLocalPipeline(
            voice_choice=os.environ.get("TTS_VOICE", "en_US-amy-medium"),
        )
    else:
        llm_endpoint = os.environ.get("AZURE_OPENAI_EASTUS2_ENDPOINT")
        llm_deployment = os.environ.get("AZURE_OPENAI_REALTIME_DEPLOYMENT")
        if not llm_endpoint or not llm_deployment:
            raise RuntimeError("Azure OpenAI realtime endpoint and deployment must be configured.")

        llm_key = os.environ.get("AZURE_OPENAI_EASTUS2_API_KEY")

        credential = None
        if not llm_key:
            if tenant_id := os.environ.get("AZURE_TENANT_ID"):
                logger.info("Using AzureDeveloperCliCredential with tenant_id %s", tenant_id)
                credential = AzureDeveloperCliCredential(tenant_id=tenant_id, process_timeout=60)
            else:
                logger.info("Using DefaultAzureCredential")
                credential = DefaultAzureCredential()

        llm_credential = AzureKeyCredential(llm_key) if llm_key else credential

        rtmt = RTMiddleTier(
            credentials=llm_credential,
            endpoint=llm_endpoint,
            deployment=llm_deployment,
            voice_choice=os.environ.get("AZURE_OPENAI_REALTIME_VOICE_CHOICE") or "coral",
        )
        if api_version := os.environ.get("AZURE_OPENAI_REALTIME_API_VERSION"):
            rtmt.api_version = api_version

    rtmt.temperature = 0.6
    rtmt.system_message = (
        "You are Dunkin's always-on virtual crew member, proudly representing Inspire Brands. "
        "Guide guests through Dunkin menu decisions, keep the tone energetic yet concise, and double-check every detail with the 'search' tool before responding. "
        "Confirm each requested beverage, bakery item, or breakfast sandwich using the 'update_order' tool only after the guest has agreed. "
        "When they ask for a recap or when the order is wrapping up, call the 'get_order' tool and read back every item ordered, then announce only the total due — do not break out subtotal or tax separately. "
        "Match the customer's language throughout the session, keep responses to one or two sentences, and invite them to personalize drinks with whipped cream ($0.50), flavor swirls ($0.75), or an extra espresso shot ($1.00) only when a signature latte or cold beverage is already in the order. "
        "Do not suggest extras for donuts or breakfast sandwiches, and never ask to pair an extra espresso shot with a donut or breakfast sandwich. "
        "If the guest uses hate speech or asks for anything blocked by responsible AI, respond immediately: 'I'm sorry, but I can't assist with that request. If you need help with Dunkin' menu items or have any other questions, please let me know.' "
        "When the guest is done ordering, always use the 'get_order' tool to read back every item, size, and quantity, then announce only the total due — do not itemize subtotal or tax. After confirming the order, close with: 'Thank you! Please pull around to the next window.' "
        "If menu information is unavailable, let them know politely and offer an alternative suggestion. "
        "Never expose implementation details, file names, or API keys. Keep things friendly, fast, and unmistakably Dunkin."
    )

    # Initialize local ChromaDB for menu search
    chroma_path = os.environ.get("CHROMA_DATA_PATH") or str(Path(__file__).parent / "chroma_data")
    chroma_collection_name = os.environ.get("CHROMA_COLLECTION_NAME") or "menu_items"
    logger.info("Loading ChromaDB from %s, collection=%s", chroma_path, chroma_collection_name)
    chroma_client = chromadb.PersistentClient(path=chroma_path)
    embedding_fn = ONNXMiniLM_L6_V2()
    chroma_collection = chroma_client.get_collection(chroma_collection_name, embedding_function=embedding_fn)

    async def _order_observer(session_id: str, summary: dict) -> None:
        await simulator.record_order_update(session_id, summary)

    attach_tools_rtmt(
        rtmt,
        chroma_collection=chroma_collection,
        order_observer=_order_observer,
    )

    rtmt.attach_to_app(app, "/realtime", simulator=simulator, crm_repo=crm_repo)

    app.router.add_get("/crm/customers", _handle_list_customers)
    app.router.add_get("/crm/customers/{customer_id}", _handle_get_customer)
    app.router.add_get("/crm/devices/{mac_address}", _handle_lookup_device)

    app.router.add_post("/simulator/spawn", spawn_car)
    app.router.add_post("/simulator/reset", reset_lane)
    app.router.add_post("/simulator/complete", complete_car)
    app.router.add_get("/simulator/demo", demo_status)
    app.router.add_post("/simulator/demo/start", start_demo_mode)
    app.router.add_post("/simulator/demo/stop", stop_demo_mode)
    app.router.add_get("/dashboard", dashboard_socket)

    current_directory = Path(__file__).parent
    guest_index = current_directory / 'static/index.html'
    crew_index = current_directory / 'static/crew/index.html'

    async def _serve_guest(_request: web.Request) -> web.StreamResponse:
        return web.FileResponse(guest_index)

    async def _serve_crew(_request: web.Request) -> web.StreamResponse:
        if not crew_index.exists():
            raise web.HTTPNotFound()
        return web.FileResponse(crew_index)

    app.router.add_get('/', _serve_guest)
    # Serve crew static assets before the SPA catch-all so JS/CSS aren't swallowed.
    app.router.add_static('/crew/assets', path=current_directory / 'static/crew/assets', name='crew_assets')
    app.router.add_get('/crew', _serve_crew)
    app.router.add_get('/crew/{tail:.*}', _serve_crew)
    app.router.add_static('/', path=current_directory / 'static', name='static')

    return app


async def _create_simulator_from_env() -> DriveThruSimulator:
    max_cars = int(os.environ.get("DRIVE_THRU_MAX_CARS", 4))
    redis_url = os.environ.get("DRIVE_THRU_REDIS_URL")
    postgres_dsn = os.environ.get("DRIVE_THRU_POSTGRES_DSN")

    state_store = None
    if redis_url:
        state_store = RedisSimulatorStateStore(redis_url)
    elif postgres_dsn:
        state_store = PostgresSimulatorStateStore(postgres_dsn)
    else:
        state_store = InMemorySimulatorStateStore()

    simulator = DriveThruSimulator(max_cars=max_cars, state_store=state_store)
    await simulator.start()
    return simulator


async def _handle_list_customers(request: web.Request) -> web.Response:
    repo: CRMRepository = request.app["crm_repo"]
    customers = [profile.model_dump() for profile in repo.list_customers()]
    return web.json_response({"customers": customers})


async def _handle_get_customer(request: web.Request) -> web.Response:
    repo: CRMRepository = request.app["crm_repo"]
    customer_id = request.match_info["customer_id"]
    profile = repo.get_customer(customer_id)
    if not profile:
        raise web.HTTPNotFound()
    return web.json_response(profile.model_dump())


async def _handle_lookup_device(request: web.Request) -> web.Response:
    repo: CRMRepository = request.app["crm_repo"]
    mac_address = request.match_info["mac_address"]
    profile = repo.get_customer_by_mac(mac_address)
    if not profile:
        raise web.HTTPNotFound()
    return web.json_response(profile.model_dump())


if __name__ == "__main__":
    host = os.environ.get("HOST", "localhost")  # Change default host to localhost
    port = int(os.environ.get("PORT", 8000))  # Change default port to 8000
    web.run_app(create_app(), host=host, port=port)
