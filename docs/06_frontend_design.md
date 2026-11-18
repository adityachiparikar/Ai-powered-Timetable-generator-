# Frontend Design
## React + Vite + shadcn/ui

### 1. Pages
| Page | File | Purpose |
|---|---|---|
| Login | `Login.tsx` | JWT authentication |
| Dashboard | `Dashboard.tsx` | Overview stats |
| Data Entry | `DataEntry.tsx` | CRUD for all entities |
| Teachers | `Teachers.tsx` | Teacher management |
| Timetables | `Timetables.tsx` | Generation and grid view |
| Constraints | `Constraints.tsx` | Config + AI Chatbot |
| Settings | `Settings.tsx` | App settings |

### 2. Key Components
- **ConstraintChatbot**: AI chat widget backed by local parser + Ollama
- **TimetableGrid**: CSS Grid schedule display
- **shadcn/ui**: Card, Button, Input, Dialog, Table, Tabs

### 3. Services
- Axios API client at `services/api.ts`
- Modules: teacherApi, courseApi, roomApi, groupApi, solverApi, aiApi

### 4. Styling
- Tailwind CSS + CSS Variables (dark/light mode)
- Lucide React icons

### 5. Dev Commands
```bash
npm run dev    # :5173
npm run build  # Production
```
