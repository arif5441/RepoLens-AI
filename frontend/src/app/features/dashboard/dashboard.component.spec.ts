import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { environment } from '../../../environments/environment';
import { DashboardComponent } from './dashboard.component';

describe('DashboardComponent', () => {
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DashboardComponent],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    httpMock = TestBed.inject(HttpTestingController);
  });

  function flushRepositories(): void {
    httpMock
      .expectOne(`${environment.apiBaseUrl}/api/v1/repositories`)
      .flush({ repositories: [] });
  }

  it('shows a loading state before the health response arrives', () => {
    const fixture = TestBed.createComponent(DashboardComponent);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Checking');
    httpMock.expectOne(`${environment.apiBaseUrl}/health`).flush({
      status: 'ok',
      api: { status: 'ok', detail: null },
      database: { status: 'ok', detail: null },
      ollama: { status: 'ok', detail: null },
    });
    flushRepositories();
  });

  it('renders status indicators once health data loads', () => {
    const fixture = TestBed.createComponent(DashboardComponent);
    fixture.detectChanges();
    httpMock.expectOne(`${environment.apiBaseUrl}/health`).flush({
      status: 'degraded',
      api: { status: 'ok', detail: null },
      database: { status: 'ok', detail: null },
      ollama: { status: 'unavailable', detail: 'ollama unreachable' },
    });
    flushRepositories();
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('API');
    expect(compiled.textContent).toContain('Database');
    expect(compiled.textContent).toContain('Ollama');
  });

  it('renders recent repositories once the list loads', () => {
    const fixture = TestBed.createComponent(DashboardComponent);
    fixture.detectChanges();
    httpMock.expectOne(`${environment.apiBaseUrl}/health`).flush({
      status: 'ok',
      api: { status: 'ok', detail: null },
      database: { status: 'ok', detail: null },
      ollama: { status: 'ok', detail: null },
    });
    httpMock.expectOne(`${environment.apiBaseUrl}/api/v1/repositories`).flush({
      repositories: [
        { repository: 'trekhleb/learn-python', chunk_count: 237, last_indexed_at: new Date().toISOString() },
      ],
    });
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('trekhleb/learn-python');
  });

  it('shows an empty state when no repositories are indexed', () => {
    const fixture = TestBed.createComponent(DashboardComponent);
    fixture.detectChanges();
    httpMock.expectOne(`${environment.apiBaseUrl}/health`).flush({
      status: 'ok',
      api: { status: 'ok', detail: null },
      database: { status: 'ok', detail: null },
      ollama: { status: 'ok', detail: null },
    });
    flushRepositories();
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('No repositories indexed yet');
  });
});
