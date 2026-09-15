import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';

import { environment } from '../../../environments/environment';
import { IngestionResponse } from '../models/ingestion.model';
import { IngestionService } from './ingestion.service';

describe('IngestionService', () => {
  let service: IngestionService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(IngestionService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('posts the URL to /api/v1/repositories/ingest', () => {
    const mockResponse: IngestionResponse = {
      repository: 'octocat/Spoon-Knife',
      branch: 'main',
      files_discovered: 3,
      files_included: 1,
      files_skipped: 2,
      skipped_reasons: { unsupported_extension: 2 },
      total_size_bytes: 780,
      truncated: false,
      files: [{ path: 'README.md', language: 'markdown', size_bytes: 780, content: null }],
    };

    service.ingest('https://github.com/octocat/Spoon-Knife').subscribe((response) => {
      expect(response).toEqual(mockResponse);
    });

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/api/v1/repositories/ingest`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ url: 'https://github.com/octocat/Spoon-Knife' });
    req.flush(mockResponse);
  });
});
