import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';

import { environment } from '../../../environments/environment';
import { RepositoryIngestionComponent } from './repository-ingestion.component';

describe('RepositoryIngestionComponent', () => {
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RepositoryIngestionComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    httpMock = TestBed.inject(HttpTestingController);
  });

  it('has a pre-filled URL and ingest enabled by default', () => {
    const fixture = TestBed.createComponent(RepositoryIngestionComponent);
    fixture.detectChanges();
    expect(fixture.componentInstance.canIngest).toBeTrue();
  });

  it('disables ingest when the URL is blank', () => {
    const fixture = TestBed.createComponent(RepositoryIngestionComponent);
    fixture.detectChanges();
    fixture.componentInstance.url = '   ';
    expect(fixture.componentInstance.canIngest).toBeFalse();
  });

  it('renders the summary and file list on success', () => {
    const fixture = TestBed.createComponent(RepositoryIngestionComponent);
    fixture.detectChanges();
    fixture.componentInstance.ingest();

    httpMock.expectOne(`${environment.apiBaseUrl}/api/v1/repositories/ingest`).flush({
      repository: 'octocat/Spoon-Knife',
      branch: 'main',
      files_discovered: 3,
      files_included: 1,
      files_skipped: 2,
      skipped_reasons: { unsupported_extension: 2 },
      total_size_bytes: 780,
      truncated: false,
      files: [{ path: 'README.md', language: 'markdown', size_bytes: 780, content: null }],
    });
    fixture.detectChanges();

    expect(fixture.componentInstance.result?.repository).toBe('octocat/Spoon-Knife');
    expect(fixture.componentInstance.skippedReasonEntries).toEqual([
      { reason: 'unsupported_extension', count: 2 },
    ]);
    expect(fixture.componentInstance.loading).toBeFalse();
  });

  it('shows an error message when ingestion fails', () => {
    const fixture = TestBed.createComponent(RepositoryIngestionComponent);
    fixture.detectChanges();
    fixture.componentInstance.ingest();

    httpMock.expectOne(`${environment.apiBaseUrl}/api/v1/repositories/ingest`).flush(
      { error: { code: 'RepositoryNotFoundError', message: 'repository not found or not accessible' } },
      { status: 404, statusText: 'Not Found' },
    );
    fixture.detectChanges();

    expect(fixture.componentInstance.errorMessage).toBe('repository not found or not accessible');
    expect(fixture.componentInstance.result).toBeNull();
  });
});
