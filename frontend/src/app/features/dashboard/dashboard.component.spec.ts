import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';

import { environment } from '../../../environments/environment';
import { DashboardComponent } from './dashboard.component';

describe('DashboardComponent', () => {
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DashboardComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    httpMock = TestBed.inject(HttpTestingController);
  });

  it('shows a loading state before the health response arrives', () => {
    const fixture = TestBed.createComponent(DashboardComponent);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Checking system status');
    httpMock.expectOne(`${environment.apiBaseUrl}/health`).flush({
      status: 'ok',
      api: { status: 'ok', detail: null },
      database: { status: 'ok', detail: null },
      ollama: { status: 'ok', detail: null },
    });
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
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelectorAll('app-status-indicator').length).toBe(3);
  });
});
