import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { EmbeddingTestRequest, EmbeddingTestResponse } from '../models/embedding.model';
import { ApiService } from './api.service';

@Injectable({ providedIn: 'root' })
export class EmbeddingService {
  constructor(private readonly api: ApiService) {}

  test(texts: string[]): Observable<EmbeddingTestResponse> {
    const request: EmbeddingTestRequest = { texts };
    return this.api.post<EmbeddingTestResponse>('/api/v1/embeddings/test', request);
  }
}
