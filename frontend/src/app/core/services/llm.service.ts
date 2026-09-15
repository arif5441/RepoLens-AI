import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { LLMChatRequest, LLMChatResponse } from '../models/llm.model';
import { ApiService } from './api.service';

@Injectable({ providedIn: 'root' })
export class LlmService {
  constructor(private readonly api: ApiService) {}

  chat(message: string): Observable<LLMChatResponse> {
    const request: LLMChatRequest = { message };
    return this.api.post<LLMChatResponse>('/api/v1/llm/chat', request);
  }
}
