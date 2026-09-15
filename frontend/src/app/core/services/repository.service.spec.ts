import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';

import { environment } from '../../../environments/environment';
import { AskResponse, IndexResponse, RepositoryListResponse } from '../models/repository.model';
import { RepositoryService } from './repository.service';

describe('RepositoryService', () => {
  let service: RepositoryService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(RepositoryService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('posts the url to /api/v1/repositories/index', () => {
    const mockResponse: IndexResponse = {
      repository: 'octocat/demo', branch: 'main', files_included: 1, chunks_created: 2,
      chunks_stored: 2, embedding_model: 'fake-model', duration_ms: 10,
    };

    service.index('https://github.com/octocat/demo').subscribe((response) => {
      expect(response).toEqual(mockResponse);
    });

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/api/v1/repositories/index`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ url: 'https://github.com/octocat/demo' });
    req.flush(mockResponse);
  });

  it('gets the repository list from /api/v1/repositories', () => {
    const mockResponse: RepositoryListResponse = {
      repositories: [{ repository: 'octocat/demo', chunk_count: 2, last_indexed_at: '2026-01-01' }],
    };

    service.list().subscribe((response) => {
      expect(response).toEqual(mockResponse);
    });

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/api/v1/repositories`);
    expect(req.request.method).toBe('GET');
    req.flush(mockResponse);
  });

  it('posts repository and question to /api/v1/repositories/ask', () => {
    const mockResponse: AskResponse = {
      repository: 'octocat/demo', question: 'q?', answer: 'a.', citations: [], grounded: true,
      model: 'phi3:mini', duration_ms: 10,
    };

    service.ask('octocat/demo', 'q?').subscribe((response) => {
      expect(response).toEqual(mockResponse);
    });

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/api/v1/repositories/ask`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ repository: 'octocat/demo', question: 'q?' });
    req.flush(mockResponse);
  });
});
