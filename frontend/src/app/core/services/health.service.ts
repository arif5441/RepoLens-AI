import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { HealthResponse } from '../models/health.model';
import { ApiService } from './api.service';

@Injectable({ providedIn: 'root' })
export class HealthService {
  constructor(private readonly api: ApiService) {}

  getHealth(): Observable<HealthResponse> {
    return this.api.get<HealthResponse>('/health');
  }
}
