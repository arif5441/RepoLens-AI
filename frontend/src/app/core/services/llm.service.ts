import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { LLMChatRequest, LLMChatResponse, LLMModelsResponse } from '../models/llm.model';
import { ApiService } from './api.service';

@Injectable({ providedIn: 'root' })
export class LlmService {
  constructor(private readonly api: ApiService) {}

  chat(message: string, systemPrompt?: string, model?: string): Observable<LLMChatResponse> {
    const request: LLMChatRequest = {
      message,
      system_prompt: systemPrompt?.trim() ? systemPrompt.trim() : null,
      model: model || null,
    };
    return this.api.post<LLMChatResponse>('/api/v1/llm/chat', request);
  }

  listModels(): Observable<LLMModelsResponse> {
    return this.api.get<LLMModelsResponse>('/api/v1/llm/models');
  }
}
