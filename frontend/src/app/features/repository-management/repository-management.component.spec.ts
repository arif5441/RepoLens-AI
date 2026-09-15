import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { environment } from '../../../environments/environment';
import { RepositoryManagementComponent } from './repository-management.component';

describe('RepositoryManagementComponent', () => {
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RepositoryManagementComponent],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();
    httpMock = TestBed.inject(HttpTestingController);
  });

  function flushList(repositories: any[] = []) {
    httpMock.expectOne(`${environment.apiBaseUrl}/api/v1/repositories`).flush({ repositories });
  }

  it('loads the repository list on init', () => {
    const fixture = TestBed.createComponent(RepositoryManagementComponent);
    fixture.detectChanges();

    flushList([{ repository: 'octocat/demo', chunk_count: 3, last_indexed_at: '2026-01-01' }]);
    fixture.detectChanges();

    expect(fixture.componentInstance.repositories.length).toBe(1);
    expect(fixture.componentInstance.listLoading).toBeFalse();
  });

  it('disables index when the url is blank', () => {
    const fixture = TestBed.createComponent(RepositoryManagementComponent);
    fixture.detectChanges();
    flushList();

    fixture.componentInstance.url = '   ';
    expect(fixture.componentInstance.canIndex).toBeFalse();
  });

  it('indexes a repository and reloads the list on success', () => {
    const fixture = TestBed.createComponent(RepositoryManagementComponent);
    fixture.detectChanges();
    flushList();

    fixture.componentInstance.indexRepository();
    httpMock.expectOne(`${environment.apiBaseUrl}/api/v1/repositories/index`).flush({
      repository: 'octocat/demo', branch: 'main', files_included: 1, chunks_created: 2,
      chunks_stored: 2, embedding_model: 'fake-model', duration_ms: 10,
    });
    flushList([{ repository: 'octocat/demo', chunk_count: 2, last_indexed_at: '2026-01-01' }]);
    fixture.detectChanges();

    expect(fixture.componentInstance.indexResult?.repository).toBe('octocat/demo');
    expect(fixture.componentInstance.repositories.length).toBe(1);
  });

  it('shows an error when indexing fails', () => {
    const fixture = TestBed.createComponent(RepositoryManagementComponent);
    fixture.detectChanges();
    flushList();

    fixture.componentInstance.indexRepository();
    httpMock.expectOne(`${environment.apiBaseUrl}/api/v1/repositories/index`).flush(
      { error: { code: 'RepositoryNotFoundError', message: 'repository not found or not accessible' } },
      { status: 404, statusText: 'Not Found' },
    );
    fixture.detectChanges();

    expect(fixture.componentInstance.indexError).toBe('repository not found or not accessible');
  });
});
