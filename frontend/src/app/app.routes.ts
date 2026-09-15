import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./features/dashboard/dashboard.component').then((m) => m.DashboardComponent),
  },
  {
    path: 'playground',
    loadComponent: () =>
      import('./features/llm-playground/llm-playground.component').then(
        (m) => m.LlmPlaygroundComponent,
      ),
  },
  {
    path: 'embeddings',
    loadComponent: () =>
      import('./features/embeddings-playground/embeddings-playground.component').then(
        (m) => m.EmbeddingsPlaygroundComponent,
      ),
  },
  {
    path: 'ingest',
    loadComponent: () =>
      import('./features/repository-ingestion/repository-ingestion.component').then(
        (m) => m.RepositoryIngestionComponent,
      ),
  },
  {
    path: 'repositories',
    loadComponent: () =>
      import('./features/repository-management/repository-management.component').then(
        (m) => m.RepositoryManagementComponent,
      ),
  },
  {
    path: 'chat',
    loadComponent: () => import('./features/chat/chat.component').then((m) => m.ChatComponent),
  },
];
