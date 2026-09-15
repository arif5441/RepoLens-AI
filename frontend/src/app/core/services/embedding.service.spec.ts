import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';

import { environment } from '../../../environments/environment';
import { EmbeddingTestResponse } from '../models/embedding.model';
import { EmbeddingService } from './embedding.service';

describe('EmbeddingService', () => {
  let service: EmbeddingService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(EmbeddingService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('posts the texts to /api/v1/embeddings/test', () => {
    const mockResponse: EmbeddingTestResponse = {
      model: 'sentence-transformers/all-MiniLM-L6-v2',
      dimension: 384,
      count: 2,
      embeddings: [[0.1], [0.2]],
      similarities: [{ text_a_index: 0, text_b_index: 1, text_a: 'a', text_b: 'b', similarity: 0.5 }],
      duration_ms: 10,
    };

    service.test(['a', 'b']).subscribe((response) => {
      expect(response).toEqual(mockResponse);
    });

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/api/v1/embeddings/test`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ texts: ['a', 'b'] });
    req.flush(mockResponse);
  });
});
