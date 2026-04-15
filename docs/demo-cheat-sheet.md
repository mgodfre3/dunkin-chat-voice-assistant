# Dunkin Demo Cheat Sheet

This page is the short version of the demo materials. Use it when you need presenter-ready talking points instead of a full technical walkthrough.

## 30-Second Version

"This is a voice ordering assistant running on Azure Local. The guest speaks into the browser, the request goes through Kubernetes ingress to an edge-hosted Python backend, and the live deployment uses Azure OpenAI Realtime for low-latency voice interaction. Menu retrieval, order state, and app logic stay local on the edge using ChromaDB and backend tools. We also support a fully-local path using Whisper, Foundry Local with Phi-4 Mini, and Piper."

## 2-Minute Version

"What makes this interesting is that it is not just a chatbot in a browser. It is an edge application running on Azure Local with a real Kubernetes deployment model. The browser opens a realtime WebSocket into the cluster, NGINX ingress preserves the upgrade headers, and the backend handles the actual session logic and tool execution.

In the public deployment, we use a hybrid path: Azure OpenAI Realtime provides fast speech-to-text, reasoning, and text-to-speech, while menu search stays local in ChromaDB. That means the voice quality and latency are strong, but the menu data plane and business logic stay on-prem.

The repo also supports a fully-local mode. In that path, Whisper performs transcription, Foundry Local hosts Phi-4 Mini for reasoning and tool use, and Piper handles text-to-speech. So the architecture can move from hybrid to local without changing the front-end experience." 

## 5-Minute Version

1. Start with the guest experience and explain that the microphone input becomes a realtime WebSocket session.
2. Explain that the active deployment is on Azure Local and is managed through Flux GitOps.
3. Call out that the current public deployment is hybrid-first: Azure OpenAI Realtime handles the live voice loop, while local ChromaDB handles menu retrieval.
4. Show that the order panel updates because the model is calling backend tools, not because the UI is simulating a cart.
5. Open the employee dashboard and explain that this demo includes operational context, not just a voice UX.
6. If you have cluster access, show the app pod, service, and ingress.
7. Then show the Foundry Local model deployment and explain that `USE_LOCAL_PIPELINE=true` switches the backend to a local speech-and-LLM pipeline.
8. End by emphasizing the tradeoff: hybrid is best for live responsiveness, and fully-local is best when cloud dependency has to be minimized.

## Fast Talking Points

- This is an edge app, not a thin web client.
- The live deployment is hybrid-first and optimized for latency.
- Menu retrieval and order logic stay local even in hybrid mode.
- Foundry Local is the optional local reasoning layer.
- The same front end can drive either the hybrid or the fully-local path.

## What To Show Live

### Guest and crew experience

1. Open the guest experience at <https://dunkin.adaptivecloudlab.com>.
2. Open the employee dashboard at <https://dunkin.adaptivecloudlab.com/crew>.
3. Place a simple order by voice.
4. Point out the order panel update and the crew-side operational view.

### Cluster view

```bash
kubectl get pods -n dunkin-voice
kubectl get svc -n dunkin-voice
kubectl get ingress -n dunkin-voice
kubectl logs deploy/dunkin-voice-assistant -n dunkin-voice -c dunkin-voice --tail=100
```

### Foundry Local view

```bash
kubectl get modeldeployments -n foundry-local-operator
kubectl describe modeldeployment phi-4-mini-gpu -n foundry-local-operator
kubectl get pods -n foundry-local-operator
```

## Likely Questions

### Why is the public deployment not fully local?

Because the hybrid path currently gives a better live voice experience. The fully-local path exists to show that the architecture can shift to local speech and reasoning when needed.

### What stays local in hybrid mode?

The app container, session state, tool execution, menu retrieval, and Kubernetes runtime all stay local. The hybrid dependency is specifically the Azure OpenAI realtime voice-and-reasoning path.

### What is Foundry Local doing here?

It hosts the local LLM endpoint used in fully-local mode. In this repo that is a Phi-4 Mini deployment surfaced as a Kubernetes-native model deployment.

## Good Closing Line

"The point of this demo is not just that voice ordering works. It is that the same edge-hosted application can either use a cloud realtime model for the best live experience or swap to a local model stack with Foundry Local when deployment constraints demand it."