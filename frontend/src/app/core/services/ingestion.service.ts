import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { IngestionRequest, IngestionResponse } from '../models/ingestion.model';
import { ApiService } from './api.service';

@Injectable({ providedIn: 'root' })
export class IngestionService {
  constructor(private readonly api: ApiService) {}

  ingest(url: string): Observable<IngestionResponse> {
    const request: IngestionRequest = { url };
    return this.api.post<IngestionResponse>('/api/v1/repositories/ingest', request);
  }
}
