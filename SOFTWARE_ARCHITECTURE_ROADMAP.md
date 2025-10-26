<!-- @format -->

# Software Architecture Roadmap

## Auto-Replenishment System for Snap Spectacles AR

### **Project:** CalHacks25 - Hands-Free Auto-Replenishment via AR Glasses

### **Date:** 2025

### **Document Version:** 1.0

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [Architecture Layers](#architecture-layers)
4. [Component Architecture](#component-architecture)
5. [Data Flow & Communication Patterns](#data-flow--communication-patterns)
6. [Technology Stack Deep Dive](#technology-stack-deep-dive)
7. [Implementation Roadmap](#implementation-roadmap)
8. [Scaling Strategy](#scaling-strategy)
9. [Security Architecture](#security-architecture)
10. [Testing Strategy](#testing-strategy)
11. [Deployment Architecture](#deployment-architecture)
12. [Monitoring & Observability](#monitoring--observability)

---

## 1. Executive Summary

### Vision

Create an intelligent, hands-free replenishment system using Snap Spectacles AR
glasses that automatically detects low inventory and enables one-gesture
reordering.

### Core Value Propositions

- **Hands-Free Experience**: Voice and gesture-based interaction
- **Real-Time Intelligence**: Live computer vision on device
- **Contextual Commerce**: Seamless product discovery and ordering
- **Zero Friction**: Sub-second latency from detection to confirmation

### Key Metrics (Target)

- **Detection Latency**: <300ms end-to-end
- **Re-order Success Rate**: >95%
- **User Confirmation Time**: <5s
- **System Uptime**: 99.9%

---

## 2. System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SPECTACLES AR LAYER                      │
│  (Snap Lens Studio → Snap OS → Hardware)                   │
├─────────────────────────────────────────────────────────────┤
│  • Hand Tracking (3D skeleton estimation)                   │
│  • Vision Processing (CV models for object detection)       │
│  • Gesture Recognition (pinch, poke, voice)                │
│  • Display & UI (AR overlays, text, voice)                  │
│  • Camera Feed → AI Vision API                              │
└─────────────────────┬───────────────────────────────────────┘
                       │
                       │ HTTP/REST + WebSockets
                       │
┌─────────────────────▼───────────────────────────────────────┐
│                   BACKEND API LAYER                          │
│  (FastAPI → Python → Business Logic)                       │
├─────────────────────────────────────────────────────────────┤
│  Layers:                                                     │
│  ├── API Gateway (FastAPI Router)                           │
│  ├── Services Layer (Orchestration)                         │
│  ├── Data Access Layer (In-Memory → Future: PostgreSQL)     │
│  └── External Integrations                                  │
└─────────────────────┬───────────────────────────────────────┘
                       │
                       │ REST + GraphQL
                       │
┌─────────────────────▼───────────────────────────────────────┐
│                EXTERNAL SERVICES LAYER                      │
├─────────────────────────────────────────────────────────────┤
│  • OpenAI (GPT-4o-mini Vision, TTS)                         │
│  • Bright Data (Amazon product scraping)                     │
│  • Commerce APIs (Amazon, Instacart, Walmart mock)          │
│  • Location Services (GPS/Indoor positioning)               │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
User Wears Spectacles
         ↓
Camera Captures Frame
         ↓
    ┌─────────────────┐
    │ Computer Vision  │  ← ML Component / Custom CV
    │ (Object + Fill)  │
    └────────┬─────────┘
             ↓
    ┌─────────────────┐
    │ Detection Event  │  → POST /api/detections
    │ (object_class,   │
    │  fill_level)    │
    └────────┬─────────┘
             ↓
    ┌─────────────────┐
    │  Intent Store    │  → Check cooldown, map to product
    │  (Throttling)    │
    └────────┬─────────┘
             ↓
    ┌─────────────────┐
    │ Prompt User      │  → "Your water bottle is low. Reorder?"
    │ (Voice/Visual)   │
    └────────┬─────────┘
             ↓
    ┌─────────────────┐
    │ User Gesture/    │  → POST /api/orders/decisions
    │ Voice Response  │
    └────────┬─────────┘
             ↓
    ┌─────────────────┐
    │ Commerce API     │  → Submit order to provider
    │ (Mock/Real)      │
    └────────┬─────────┘
             ↓
    ┌─────────────────┐
    │ Confirm to User  │  → "Order placed! Arriving Friday."
    │ (TTS + Visual)   │
    └─────────────────┘
```

---

## 3. Architecture Layers

### 3.1 Presentation Layer (AR Frontend)

**Technology:** Lens Studio + Spectacles Interaction Kit (SIK)

**Components:**

| Component              | Technology            | Responsibility                                    |
| ---------------------- | --------------------- | ------------------------------------------------- |
| **VisionOpenAI**       | TypeScript/JavaScript | Orchestrates vision API calls, handles user input |
| **TextToSpeechOpenAI** | TypeScript/JavaScript | Converts LLM responses to speech                  |
| **CameraAPI**          | JavaScript            | Captures camera texture for CV processing         |
| **SpeechToText**       | JavaScript            | Transcribes voice commands                        |
| **HandVisual**         | SIK Component         | 3D hand tracking & gesture recognition            |
| **ContainerFrame**     | SIK Component         | UI container with follow/pinch interactions       |
| **Interactable**       | SIK Component         | Base for pinch/tap/voice input handling           |
| **HttpClient**         | TypeScript            | HTTP communication with backend                   |

**Key Patterns:**

- **Component-based architecture**: Reusable ScriptComponents
- **Event-driven**: onTriggerEnd, onStart, UpdateEvent
- **Decorator pattern**: `@component`, `@input` for dependency injection
- **Observer pattern**: Event binding for user interactions

### 3.2 Application Layer (Backend API)

**Technology:** FastAPI + Python

**Layers:**

```
┌─────────────────────────────────────────────────────────┐
│                    API ROUTING LAYER                     │
│  (app/api/routes.py → endpoints/*.py)                   │
├─────────────────────────────────────────────────────────┤
│  • /api/detections        → Detection handling          │
│  • /api/orders            → Order lifecycle             │
│  • /api/products          → Catalog queries           │
│  • /api/scrapers/amazon   → Product discovery            │
│  • /api/system/telemetry  → Observability                │
└─────────────────────┬───────────────────────────────────┘
                       ↓
┌─────────────────────▼───────────────────────────────────────┐
│                  SERVICES LAYER                            │
│  (app/services/*.py)                                       │
├─────────────────────────────────────────────────────────────┤
│  ├── ProductCatalogService                                 │
│  │   • Object class → Product mapping                       │
│  │   • Variant resolution                                   │
│  │   • Reorder threshold logic                              │
│  │                                                          │
│  ├── PromptIntentStore                                      │
│  │   • Detection ingestion                                 │
│  │   • Cooldown throttling                                  │
│  │   • Intent lifecycle management                          │
│  │   • Order state tracking                                 │
│  │                                                          │
│  ├── CommerceProvider                                       │
│  │   • Mock commerce mode                                   │
│  │   • Real API integration (future)                       │
│  │   • Order submission & status                            │
│  │                                                          │
│  ├── BrightDataScraper                                      │
│  │   • Amazon product discovery                            │
│  │   • Keyword search                                       │
│  │   • Product metadata extraction                          │
│  │                                                          │
│  └── TelemetryClient                                        │
│      • Event aggregation                                    │
│      • Performance metrics                                  │
│      • Debug information                                    │
└─────────────────────┬───────────────────────────────────────┘
                       ↓
┌─────────────────────▼───────────────────────────────────────┐
│                  DATA MODELS LAYER                         │
│  (Pydantic schemas + in-memory storage)                    │
├─────────────────────────────────────────────────────────────┤
│  • DetectionEvent                                           │
│  • PromptIntent                                             │
│  • OrderRecord                                              │
│  • Product + ProductVariant                                │
│  • BrightDataScrapeResponse                                 │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 Integration Layer

**External APIs:**

- **OpenAI**: GPT-4o-mini Vision API, Text-to-Speech API
- **Bright Data**: Amazon product scraping dataset API
- **Location Services**: RawLocationModule (GPS coordinates)
- **Commerce APIs**: Placeholder for real integrations

**Communication Patterns:**

- **HTTP REST** (primary): JSON payloads
- **WebSocket** (future): Real-time order status updates
- **GraphQL** (future): Flexible product catalog queries

---

## 4. Component Architecture

### 4.1 Frontend Components (Lens Studio)

#### VisionOpenAI Component

```typescript
@component
export class VisionOpenAI {
	// Inputs
	@input textInput: Text
	@input textOutput: Text
	@input image: Image
	@input interactable: Interactable
	@input ttsComponent: TextToSpeechOpenAI
	@input chatHistoryText: Text

	// Configuration
	@input backendBaseUrl: string = 'http://localhost:8000'
	@input maxHistoryLength: number = 10

	// Dependencies
	private httpClient: HttpClient
	private locationService: LocationService
	private chatHistory: string[]

	// Methods
	async handleTriggerEnd(event: InteractorEvent)
	async orchestrateAI(userQuery: string, base64Image: string)
	private updateLocation()
	private getChatHistoryString(): string
}
```

**Responsibilities:**

- Capture camera texture as base64 image
- Send vision + text prompt to backend `/api/orchestrate`
- Manage conversation history (last N turns)
- Handle location context
- Trigger TTS responses

**Data Flow:**

```
User Pinch Gesture
      ↓
onTriggerEnd()
      ↓
Encode camera frame → base64
      ↓
POST {user_prompt, image_surroundings, chat_history, lat/long}
      ↓
Backend orchestrates → OpenAI GPT-4o-mini Vision
      ↓
Return response → Update UI + Send to TTS
```

#### ContainerFrame (UI Component)

**Purpose:** Window-like UI container for AR content

**Key Features:**

- **Follow Button**: Toggles billboarding/following behavior
- **Close Button**: Dismisses frame
- **Pinch/Gesture Interaction**: Full SIK hand tracking
- **Responsive Scaling**: User can resize with gestures
- **Auto Show/Hide**: Appears on hand proximity

**Architecture Pattern:**

- **MVC**: Model (frame state) ↔ View (visual) ↔ Controller (interactions)
- **State Management**: `isFollowing`, `isVisible`, `isSnapping`
- **Behavior Composition**: SmoothFollow, SnappableBehavior

#### HandVisual Component

**Purpose:** 3D hand tracking visualization

**Configuration:**

- **Hand Type**: Left/Right
- **Visual Mode**: Default/Occluder
- **Joint Mapping**: Automatic vs Manual
- **Glow Effects**: Poke/pinch visual feedback

### 4.2 Backend Components (FastAPI)

#### Detection Endpoint (`/api/detections`)

```python
@router.post("")
async def ingest_detection(event: DetectionEvent):
    # 1. Validate product exists in catalog
    product = catalog.get_by_object_class(event.object_class)

    # 2. Resolve product variant
    variant = catalog.resolve_variant(event.object_class, None)

    # 3. Emit telemetry
    telemetry.emit("detection", ...)

    # 4. Register with intent store (throttling logic)
    response = await intent_store.register_detection(event, product, variant)

    return response  # {should_prompt, intent_id, cooldown}
```

**Decision Logic:**

- Is product in catalog? → 404 if unknown
- Should prompt? → Check fill_level vs reorder_threshold
- Cooldown active? → Return existing intent_id
- New intent? → Generate intent_id, expiry timestamp

#### Intent Store Service

```python
class PromptIntentStore:
    def __init__(self,
                 prompt_cooldown_ms: int = 5 * 60 * 1000,
                 intent_ttl_ms: int = 15 * 60 * 1000):
        self._state: Dict[str, IntentState] = {}
        self._orders: Dict[str, OrderRecord] = {}
        self._lock = asyncio.Lock()

    async def register_detection(...) -> DetectionIngestResponse
    async def get_intent(intent_id: str) -> Optional[IntentState]
    async def record_decision(...) -> PromptDecisionResponse
    async def mark_order_submitted(...)
```

**State Machine:**

```
DETECTION → [Throttle Check] → [Create Intent] → PENDING
                                                         ↓
                                              USER DECISION → [PENDING/REJECTED]
                                                             ↓
                                                      [Order Submit] → SUBMITTED
                                                                        ↓
                                                              CONFIRMED/FAILED
```

#### Product Catalog Service

**Data Structure:**

```python
class Product:
    id: str
    object_class: str  # "water_bottle", "sunscreen", "soap_dispenser"
    default_variant: ProductVariant
    variants: List[ProductVariant]
    reorder_threshold: FillLevel  # NEARLY_EMPTY, EMPTY
    metadata: Dict[str, str]  # provider: "amazon"

class ProductVariant:
    sku: str
    label: str
    size: Optional[str]
    unit_price_usd: Optional[float]
```

**Current Catalog:**

- **water_bottle** → Spring Water 24-pack ($12.99)
- **sunscreen** → SPF 50 Sunscreen ($15.49)
- **soap_dispenser** → Foaming Soap Refill ($9.99)

#### Commerce Provider

**Abstraction Pattern:**

```python
class CommerceProvider:
    async def submit_order(request: OrderRequest) -> OrderRecord
```

**Modes:**

1. **Mock Mode** (default): Returns fake order_id, status=CONFIRMED
2. **Real API** (future): Calls commerce API, returns real order_id

**Current Implementation:**

- Always mock (for demo/hackathon)
- Real integrations would require OAuth, API keys per provider

---

## 5. Data Flow & Communication Patterns

### 5.1 Detection Flow

```
┌────────────────┐
│ User Views     │
│ Water Bottle   │
│ (Spectacles)   │
└───────┬────────┘
        │
        ↓ [Camera captures frame]
┌────────────────┐
│ Computer       │
│ Vision Model   │ → Detects object_class="water_bottle"
│ (on-device)    │ → Estimates fill_level="NEARLY_EMPTY"
└───────┬────────┘
        │
        ↓ [Create DetectionEvent]
┌─────────────────────────────────────────────────────┐
│ DetectionEvent {                                      │
│   event_id: "abc123...",                             │
│   device_id: "device_001",                           │
│   object_class: "water_bottle",                      │
│   fill_level: "NEARLY_EMPTY",                        │
│   confidence: "HIGH",                                │
│   captured_at_ms: 1699123456789                     │
│ }                                                     │
└───────┬──────────────────────────────────────────────┘
        │
        ↓ [POST /api/detections]
┌─────────────────────▼─────────────────────────────────┐
│ Backend Processing                                    │
│ ├─ Validate event_id uniqueness                       │
│ ├─ Lookup product by object_class                     │
│ ├─ Resolve variant (SKU)                             │
│ ├─ Check cooldown (5min window)                      │
│ ├─ Check reorder_threshold                           │
│ └─ Generate PromptIntent                              │
└─────────────────────┬─────────────────────────────────┘
        │
        ↓ [Response: {should_prompt: true, intent_id}]
┌────────────────┐
│ Show Prompt    │ → "Your water is low. Reorder?"
│ to User        │
└────────────────┘
```

### 5.2 Order Decision Flow

```
┌────────────────┐
│ User Gestures  │ → Pinch gesture on "Yes"
│ YES or NO      │   OR
│                │ → Voice: "Yes, reorder"
└───────┬────────┘
        │
        ↓ [Create PromptDecisionRequest]
┌─────────────────────────────────────────────────────┐
│ PromptDecisionRequest {                              │
│   intent_id: "xyz789...",                            │
│   channel: "GESTURE" | "VOICE",                       │
│   accepted: true,                                    │
│   decided_at_ms: 1699123457890                      │
│ }                                                     │
└───────┬──────────────────────────────────────────────┘
        │
        ↓ [POST /api/orders/decisions]
┌─────────────────────▼─────────────────────────────────┐
│ Backend Processing                                    │
│ ├─ Validate intent exists & not expired              │
│ ├─ Update IntentState.accepted = true                │
│ ├─ Create OrderRequest                               │
│ ├─ Call CommerceProvider.submit_order()              │
│ ├─ Record order in IntentState                       │
│ └─ Return order_id + status                          │
└─────────────────────┬─────────────────────────────────┘
        │
        ↓ [Response: {order_id, status, message}]
┌────────────────┐
│ Confirm to     │ → TTS: "Order placed! Arriving Fri."
│ User           │
└────────────────┘
```

### 5.3 AI Orchestration Flow

```
┌────────────────┐
│ User Query     │ → "What's in my fridge?"
│ (via Voice)    │
└───────┬────────┘
        │
        ↓ [Capture camera frame]
┌────────────────┐
│ Encode Image   │ → base64 JPEG
│ (VisionOpenAI) │
└───────┬────────┘
        │
        ↓ [POST /api/orchestrate]
┌─────────────────────────────────────────────────────────┐
│ Payload {                                               │
│   user_prompt: "What's in my fridge?",                 │
│   image_surroundings: "data:image/jpeg;base64...",     │
│   latitude: 37.7749,                                    │
│   longitude: -122.4194,                                 │
│   chat_history: "..."                                   │
│ }                                                        │
└───────┬─────────────────────────────────────────────────┘
        │
        ↓ [Backend orchestrates]
┌─────────────────────▼────────────────────────────────┐
│ Call OpenAI GPT-4o-mini Vision API                     │
│ ├─ Create messages array with history                 │
│ ├─ Attach base64 image                                │
│ ├─ Include system prompt: "Helpful AI assistant..."   │
│ └─ Stream response                                    │
└─────────────────────┬────────────────────────────────┘
        │
        ↓ [Response: LLM text]
┌─────────────────────────────────────────────────────────┐
│ Response Processing                                     │
│ ├─ Parse LLM response text                            │
│ ├─ Update chat history                                 │
│ ├─ Format for display (wrap text)                     │
│ └─ Return to Lens                                     │
└─────────────────────┬───────────────────────────────────┘
        │
        ↓ [Frontend receives]
┌───────────────────────────────────────────────────────┐
│ Frontend Processing                                     │
│ ├─ Update textOutput UI component                     │
│ ├─ Update LLM_analyse component                        │
│ ├─ Update chatHistoryText                              │
│ └─ Call TextToSpeechOpenAI.speak(text)                 │
└─────────────────────┬───────────────────────────────────┘
        │
        ↓
┌────────────────┐
│ User Hears     │ → TTS: "I can see... 3 items..."
│ Response       │
└────────────────┘
```

---

## 6. Technology Stack Deep Dive

### 6.1 Frontend (Spectacles AR)

| Technology                     | Version | Purpose            | Status     |
| ------------------------------ | ------- | ------------------ | ---------- |
| **Lens Studio**                | Latest  | AR development IDE | ✅ Active  |
| **Spectacles Interaction Kit** | v0.10.0 | Hand tracking, UI  | ✅ Active  |
| **TypeScript**                 | ES2021  | Primary scripting  | ✅ Active  |
| **JavaScript**                 | ES6+    | Legacy scripts     | ✅ Active  |
| **ML Component**               | -       | On-device CV       | 🔄 Planned |
| **TensorFlow Lite**            | -       | CV models          | 🔄 Planned |

**Key Libraries:**

- `HttpClient` (custom) - HTTP abstraction
- `SIK.InteractionManager` - Global interaction state
- `RawLocationModule` - GPS coordinates

### 6.2 Backend (FastAPI)

| Technology        | Version  | Purpose         | Status    |
| ----------------- | -------- | --------------- | --------- |
| **Python**        | 3.8+     | Runtime         | ✅ Active |
| **FastAPI**       | 0.115.12 | Web framework   | ✅ Active |
| **Uvicorn**       | 0.34.2   | ASGI server     | ✅ Active |
| **Pydantic**      | 2.11.3   | Data validation | ✅ Active |
| **requests**      | 2.31.0   | HTTP client     | ✅ Active |
| **python-dotenv** | 1.0.0    | Env config      | ✅ Active |

**Middleware:**

- CORS (allow all origins for demo)
- Async request handling

**Future Dependencies:**

- `postgresql` - Database
- `redis` - Caching & queues
- `celery` - Background tasks
- `pytest` - Testing

### 6.3 AI/ML Services

| Service       | Model       | Purpose               | Status     |
| ------------- | ----------- | --------------------- | ---------- |
| **OpenAI**    | GPT-4o-mini | Vision + chat         | ✅ Active  |
| **OpenAI**    | TTS-1       | Text-to-speech        | ✅ Active  |
| **Custom CV** | -           | Object detection      | 🔄 Planned |
| **Custom CV** | -           | Fill level estimation | 🔄 Planned |

**Future ML Models:**

- YOLOv8 (object detection)
- EfficientDet (fill level)
- MediaPipe (hand tracking) - already in SIK

---

## 7. Implementation Roadmap

### Phase 1: MVP (Current) ✅

**Timeline:** Completed

**Deliverables:**

- ✅ FastAPI backend with core endpoints
- ✅ Lens Studio frontend with SIK integration
- ✅ Vision AI (OpenAI GPT-4o-mini)
- ✅ Voice interaction (TTS/STT)
- ✅ Gesture handling (pinch)
- ✅ Mock commerce provider
- ✅ Telemetry system

**Features:**

- Detection ingestion
- Intent store with cooldown
- Order decision handling
- Product catalog (3 items)
- Bright Data scraper integration
- Location context

### Phase 2: Enhanced AI & CV (Next)

**Timeline:** 2-3 weeks

**Deliverables:**

1. **On-Device Computer Vision**

   - Deploy TensorFlow Lite model to Lens Studio
   - Object detection pipeline (water bottle, soap, etc.)
   - Fill level estimation model
   - Real-time frame processing

2. **Improved AI Orchestration**

   - Multi-turn conversation memory
   - Context-aware responses
   - Product recommendation engine
   - Price comparison across providers

3. **Enhanced Product Catalog**

   - Expand to 20+ product categories
   - Dynamic pricing from commerce APIs
   - Supplier availability checking
   - User preference learning

4. **Advanced UI/UX**
   - Multi-item comparison views
   - Augmented product visualization
   - Order tracking overlay
   - Historical purchase data

### Phase 3: Real Commerce Integration (Weeks 4-6)

**Deliverables:**

1. **Commerce Provider Abstractions**

   - Amazon Product Advertising API
   - Instacart API integration
   - Walmart Marketplace API
   - Stripe for payment processing

2. **Order Lifecycle Management**

   - Order confirmation emails
   - Shipping tracking integration
   - Delivery notifications
   - Refund handling

3. **User Account System**
   - Device registration
   - User preferences storage
   - Address book management
   - Payment method storage

### Phase 4: Scale & Production (Weeks 7-10)

**Deliverables:**

1. **Database Migration**

   - PostgreSQL for persistent storage
   - Redis for caching
   - Migration scripts

2. **Background Job Processing**

   - Celery for async tasks
   - Order retry logic
   - Batch product updates
   - Telemetry aggregation

3. **API Gateway & Load Balancing**

   - Nginx reverse proxy
   - Rate limiting
   - Circuit breakers
   - Health checks

4. **Monitoring & Observability**
   - Prometheus metrics
   - Grafana dashboards
   - Sentry error tracking
   - PagerDuty alerts

### Phase 5: Advanced Features (Weeks 11-15)

**Deliverables:**

1. **ML Model Training Pipeline**

   - Automated dataset collection
   - Model versioning (DVC, MLflow)
   - A/B testing framework
   - Model performance monitoring

2. **Personalization Engine**

   - User preference learning (ML)
   - Dynamic product recommendations
   - Budget-aware suggestions
   - Seasonal adjustments

3. **Social Features**

   - Share shopping lists
   - Group ordering
   - Community product reviews
   - Friend recommendations

4. **Smart Notifications**
   - Predictive reordering
   - Price drop alerts
   - Bundle suggestions
   - Sustainability insights

---

## 8. Scaling Strategy

### Horizontal Scaling

```
┌─────────────────────────────────────────────────────────┐
│                    Load Balancer                        │
│                  (Nginx/CloudFlare)                     │
└───────────────────────┬─────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
┌───────▼──────┐  ┌───────▼──────┐  ┌───────▼──────┐
│  FastAPI     │  │  FastAPI     │  │  FastAPI     │
│  Instance 1  │  │  Instance 2  │  │  Instance 3  │
│              │  │              │  │              │
│  - Uvicorn   │  │  - Uvicorn   │  │  - Uvicorn   │
│  - Python 3  │  │  - Python 3   │  │  - Python 3  │
└───────┬──────┘  └───────┬──────┘  └───────┬──────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          │
                  ┌───────▼────────┐
                  │   PostgreSQL   │
                  │   (Primary)   │
                  └───────┬────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
┌───────▼──────┐  ┌───────▼──────┐  ┌───────▼──────┐
│   Redis      │  │   Redis      │  │   Redis      │
│   (Cache)    │  │   (Cache)    │  │   (Cache)    │
└──────────────┘  └──────────────┘  └──────────────┘
```

### Database Scaling Strategy

**Current:** In-memory dictionaries (MVP)

**Phase 1 → 2:**

- Migrate to PostgreSQL
- Use connection pooling (pgBouncer)
- Add database indexes:
  - `detections(device_id, object_class, captured_at_ms)`
  - `intents(intent_id, expires_at_ms)`
  - `orders(order_id, status)`

**Phase 2 → 3:**

- PostgreSQL read replicas
- Sharding by device_id hash
- Redis caching layer for hot data

### API Rate Limiting

```
┌─────────────────────────────────────────────────────────┐
│              Rate Limiting Strategy                      │
├─────────────────────────────────────────────────────────┤
│  Per Device:     100 requests/min                       │
│  Per IP:         1000 requests/min                      │
│  OpenAI API:     500 requests/min                       │
│  Bright Data:    20 requests/min                        │
│                                                          │
│  Implementation:                                        │
│  ├─ Redis-based rate limiter (sliding window)          │
│  ├─ FastAPI dependencies with @limiter                  │
│  └─ Circuit breaker for external APIs                   │
└─────────────────────────────────────────────────────────┘
```

---

## 9. Security Architecture

### Authentication & Authorization

```
┌─────────────────────────────────────────────────────────┐
│              Security Layers                            │
├─────────────────────────────────────────────────────────┤
│  1. Transport Security                                  │
│     ├─ HTTPS/TLS 1.3 mandatory                         │
│     ├─ Certificate pinning (Spectacles)               │
│     └─ Secure WebSocket (future)                       │
│                                                          │
│  2. API Security                                        │
│     ├─ OAuth 2.0 (device registration)                 │
│     ├─ API keys (per-device, rotated monthly)          │
│     ├─ JWT tokens (short-lived, refreshable)            │
│     └─ Request signing (HMAC-SHA256)                   │
│                                                          │
│  3. Data Protection                                     │
│     ├─ Encryption at rest (AES-256)                    │
│     ├─ Encryption in transit (TLS)                      │
│     ├─ PII redaction in logs                            │
│     └─ GDPR compliance (EU users)                      │
│                                                          │
│  4. Commerce Security                                    │
│     ├─ PCI DSS compliance (if handling cards)          │
│     ├─ Tokenized payment storage                        │
│     ├─ Fraud detection (ML models)                      │
│     └─ Order amount limits ($500/user/day)             │
└─────────────────────────────────────────────────────────┘
```

### Threat Model

| Threat             | Mitigation                                  |
| ------------------ | ------------------------------------------- |
| **DDoS**           | CloudFlare, rate limiting, circuit breakers |
| **API Key Theft**  | Short-lived tokens, IP whitelisting, MFA    |
| **Man-in-Middle**  | TLS 1.3, certificate pinning                |
| **Replay Attacks** | Nonce/timestamp validation                  |
| **SQL Injection**  | Pydantic validation, parameterized queries  |
| **XSS**            | Input sanitization, CSP headers             |

---

## 10. Testing Strategy

### Testing Pyramid

```
                    ┌─────────────┐
                    │     E2E      │  ← 5 tests (Spectacles → Backend)
                    │   Testing   │     • User flow: detection → order
                    └─────────────┘     • Integration with real APIs
                ┌───────────────────┐
                │   Integration     │  ← 20 tests
                │   Testing         │     • API endpoints
                │                   │     • Services integration
                └───────────────────┘
        ┌───────────────────────────────────┐
        │         Unit Testing              │  ← 100+ tests
        │                                   │     • Individual functions
        │  - Pytest (Python)               │     • Business logic
        │  - Jest (TypeScript)              │     • Mock dependencies
        └───────────────────────────────────┘
```

### Test Coverage Goals

- **Unit Tests**: >80% coverage
- **Integration Tests**: >70% coverage
- **E2E Tests**: Critical paths (5-10 flows)

### CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on: [push, pull_request]

jobs:
  lint:
    - Black formatting
    - MyPy type checking
    - ESLint (TypeScript)

  test:
    - Pytest unit tests
    - Jest frontend tests
    - Integration tests (Docker compose)

  build:
    - Docker image for FastAPI
    - Lens Studio package
    - Upload to registry

  deploy:
    - Staging → AWS/GCP
    - Prod → Blue/Green deployment
```

---

## 11. Deployment Architecture

### Deployment Pipeline

```
Developer Push
      ↓
┌────────────────┐
│  GitHub Actions│  → Lint, Test, Build
└───────┬────────┘
        ↓
┌────────────────┐
│  Docker Build  │  → Multi-stage build
└───────┬────────┘
        ↓
┌────────────────┐
│ Container Reg  │  → AWS ECR / GCP GCR
└───────┬────────┘
        ↓
┌────────────────┐
│  Deploy to     │
│  Kubernetes /  │  → Rolling update
│  ECS / Cloud   │
└────────────────┘
```

### Infrastructure (Production)

**Backend:**

- **Compute**: AWS ECS Fargate / Google Cloud Run
- **Database**: AWS RDS (PostgreSQL) / Cloud SQL
- **Cache**: AWS ElastiCache (Redis) / Memorystore
- **Load Balancer**: AWS ALB / GCP Cloud Load Balancing
- **CDN**: CloudFlare / AWS CloudFront

**Monitoring:**

- **APM**: Datadog / New Relic
- **Logs**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **Metrics**: Prometheus + Grafana
- **Alerts**: PagerDuty

**Lens Studio:**

- Deploy via Snap's lens studio wireless deploy
- Version tagging in lens studio hub
- A/B testing via split deployments

---

## 12. Monitoring & Observability

### Key Metrics

**System Metrics:**

- Request latency (p50, p95, p99)
- API error rates
- CPU/Memory utilization
- Database query time

**Business Metrics:**

- Detection → prompt conversion rate
- Prompt acceptance rate
- Order success rate
- Average order value (AOV)

**User Metrics:**

- Active devices
- Daily active users (DAU)
- Reorder frequency
- User retention

### Observability Stack

```
┌─────────────────────────────────────────────────────────┐
│              Observability Architecture                 │
├─────────────────────────────────────────────────────────┤
│  Logging:                                               │
│  ├─ Structured JSON logs (JSON logging)                 │
│  ├─ Centralized in ELK / CloudWatch                    │
│  └─ Log levels: DEBUG, INFO, WARNING, ERROR            │
│                                                          │
│  Metrics:                                               │
│  ├─ Prometheus (time-series)                           │
│  ├─ Grafana dashboards                                  │
│  └─ Custom metrics: detection_rate, order_success       │
│                                                          │
│  Tracing:                                               │
│  ├─ OpenTelemetry / Jaeger                             │
│  └─ Distributed tracing across services                 │
│                                                          │
│  Alerts:                                                │
│  ├─ PagerDuty integration                              │
│  ├─ Slack notifications                                 │
│  └─ Email alerts (critical only)                       │
└─────────────────────────────────────────────────────────┘
```

### Dashboards

**Developer Dashboard:**

- API latency trends
- Error rates by endpoint
- Database query performance
- Background job status

**Business Dashboard:**

- User acquisition trends
- Reorder rate over time
- Most popular products
- Revenue projections

**Operations Dashboard:**

- System health (CPU, memory, disk)
- Active users
- API throughput
- Error rate by service

---

## Appendix: Quick Start Guide

### Backend Setup

```bash
# Clone repository
git clone <repo>
cd fastapi-server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup (Lens Studio)

1. Open Lens Studio
2. Open project: `lens-studio/AIAssistant.esproj`
3. Enable LeftHandVisual component (if disabled)
4. Set backend URL in VisionOpenAI component
5. Deploy wirelessly to Spectacles

### Environment Variables

```bash
# Backend (.env)
OPENAI_API_KEY=sk-...
BRIGHTDATA_API_KEY=...
BRIGHTDATA_DATASET_ID=...
COMMERCE_BASE_URL=https://api.example.com
COMMERCE_API_KEY=...

# Lens Studio (Inspector)
backendBaseUrl=http://localhost:8000  # or production URL
```

---

## Conclusion

This architecture roadmap provides a comprehensive blueprint for scaling the
auto-replenishment system from MVP to production. The system is designed for:

- **Reliability**: Async processing, error handling, circuit breakers
- **Scalability**: Horizontal scaling, database sharding, caching
- **Security**: OAuth, encryption, rate limiting
- **Observability**: Logging, metrics, tracing
- **Maintainability**: Modular design, test coverage, documentation

**Next Steps:**

1. Implement on-device CV models (Phase 2)
2. Migrate to PostgreSQL (Phase 2)
3. Add real commerce integrations (Phase 3)
4. Deploy to cloud infrastructure (Phase 4)

---

**Document Maintainer:** Development Team  
**Last Updated:** 2025  
**Version:** 1.0
