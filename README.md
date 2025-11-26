
**Vanilla JS + SSE over React**: Keeping the frontend minimal reduces build complexity while SSE (Server-Sent Events) provides native browser support for real-time updates without WebSocket overhead. SSE is unidirectional (server→client), which perfectly matches our progress streaming use case, and works through HTTP (no special proxy configuration needed).

## Quick Start

*Development and deployment instructions will be added in later steps*

## Architecture

*Architecture diagram and scaling notes will be added in Step 11*

## Project Status

This project is being built incrementally following a structured implementation plan:

- [x] Step 0: Repository scaffold
- [ ] Step 1: Stack selection & justification
- [ ] Step 2: Database schema & migrations
- [ ] Step 3: API & authentication skeleton
- [ ] Step 4: UI upload & real-time progress
- [ ] Step 5: Streaming import pipeline
- [ ] Step 6: Product management UI
- [ ] Step 7: Bulk delete background job
- [ ] Step 8: Webhooks & reliable delivery
- [ ] Step 9: Tests & CI
- [ ] Step 10: Docker & local development
- [ ] Step 11: Deployment & documentation

## License

MIT
