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

  it('posts the message to /api/v1/llm/chat', () => {
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
    expect(req.request.body).toEqual({ message: 'Explain dependency injection.' });
    req.flush(mockResponse);
  });
});
