import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';

import { environment } from '../../../environments/environment';
import { LLMChatResponse } from '../models/llm.model';
import { LlmService } from './llm.service';

describe('LlmService', () => {
  let service: LlmService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(LlmService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('posts the message to /api/v1/llm/chat with no system prompt or model override', () => {
    const mockResponse: LLMChatResponse = {
      response: 'DI is...',
      model: 'phi3:mini',
      provider: 'ollama',
      duration_ms: 42,
    };

    service.chat('Explain dependency injection.').subscribe((response) => {
      expect(response).toEqual(mockResponse);
    });

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/api/v1/llm/chat`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({
      message: 'Explain dependency injection.',
      system_prompt: null,
      model: null,
    });
    req.flush(mockResponse);
  });

  it('includes a trimmed system prompt and model override when given', () => {
    service.chat('hello', '  You are a pirate.  ', 'llama3.2:3b').subscribe();

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/api/v1/llm/chat`);
    expect(req.request.body).toEqual({
      message: 'hello',
      system_prompt: 'You are a pirate.',
      model: 'llama3.2:3b',
    });
    req.flush({ response: 'ok', model: 'llama3.2:3b', provider: 'ollama', duration_ms: 1 });
  });

  it('lists available models from /api/v1/llm/models', () => {
    service.listModels().subscribe((response) => {
      expect(response.models).toEqual(['phi3:mini', 'llama3.2:3b']);
    });

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/api/v1/llm/models`);
    expect(req.request.method).toBe('GET');
    req.flush({ models: ['phi3:mini', 'llama3.2:3b'] });
  });
});
