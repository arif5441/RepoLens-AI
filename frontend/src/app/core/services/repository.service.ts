import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import {
  AskRequest,
  AskResponse,
  ExplainFileRequest,
  ExplainFileResponse,
  IndexRequest,
  IndexResponse,
  RepositoryListResponse,
} from '../models/repository.model';
import { ApiService } from './api.service';

@Injectable({ providedIn: 'root' })
export class RepositoryService {
  constructor(private readonly api: ApiService) {}

  index(url: string): Observable<IndexResponse> {
    const request: IndexRequest = { url };
    return this.api.post<IndexResponse>('/api/v1/repositories/index', request);
  }

  list(): Observable<RepositoryListResponse> {
    return this.api.get<RepositoryListResponse>('/api/v1/repositories');
  }

  ask(repository: string, question: string): Observable<AskResponse> {
    const request: AskRequest = { repository, question };
    return this.api.post<AskResponse>('/api/v1/repositories/ask', request);
  }

  explainFile(repository: string, path: string): Observable<ExplainFileResponse> {
    const request: ExplainFileRequest = { repository, path };
    return this.api.post<ExplainFileResponse>('/api/v1/repositories/explain', request);
  }
}
