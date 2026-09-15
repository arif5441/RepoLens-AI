import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    data: { title: 'Home' },
    loadComponent: () =>
      import('./features/dashboard/dashboard.component').then((m) => m.DashboardComponent),
  },
  {
    path: 'playground',
    data: { title: 'LLM Playground' },
    loadComponent: () =>
      import('./features/llm-playground/llm-playground.component').then(
        (m) => m.LlmPlaygroundComponent,
      ),
  },
  {
    path: 'embeddings',
    data: { title: 'Embeddings Playground' },
    loadComponent: () =>
      import('./features/embeddings-playground/embeddings-playground.component').then(
        (m) => m.EmbeddingsPlaygroundComponent,
      ),
  },
  {
    path: 'ingest',
    data: { title: 'Repository Ingestion (Diagnostic)' },
    loadComponent: () =>
      import('./features/repository-ingestion/repository-ingestion.component').then(
        (m) => m.RepositoryIngestionComponent,
      ),
  },
  {
    path: 'repositories',
    data: { title: 'Repositories' },
    loadComponent: () =>
      import('./features/repository-management/repository-management.component').then(
        (m) => m.RepositoryManagementComponent,
      ),
  },
  {
    path: 'chat',
    data: { title: 'Chat' },
    loadComponent: () => import('./features/chat/chat.component').then((m) => m.ChatComponent),
  },
];
