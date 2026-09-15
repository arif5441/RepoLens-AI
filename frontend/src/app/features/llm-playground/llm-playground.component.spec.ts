import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';

import { environment } from '../../../environments/environment';
import { LlmPlaygroundComponent } from './llm-playground.component';

describe('LlmPlaygroundComponent', () => {
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LlmPlaygroundComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    httpMock = TestBed.inject(HttpTestingController);
  });

  function setMessage(fixture: any, value: string) {
    fixture.componentInstance.message = value;
  }

  it('disables send when the message is empty', () => {
    const fixture = TestBed.createComponent(LlmPlaygroundComponent);
    fixture.detectChanges();
    expect(fixture.componentInstance.canSend).toBeFalse();
  });

  it('enables send once a non-empty message is entered', () => {
    const fixture = TestBed.createComponent(LlmPlaygroundComponent);
    fixture.detectChanges();
    setMessage(fixture, 'Explain DI');
    expect(fixture.componentInstance.canSend).toBeTrue();
  });

  it('shows a loading state and disables send while the request is in flight', () => {
    const fixture = TestBed.createComponent(LlmPlaygroundComponent);
    fixture.detectChanges();
    setMessage(fixture, 'Explain DI');

    fixture.componentInstance.send();
    fixture.detectChanges();

    expect(fixture.componentInstance.loading).toBeTrue();
    expect(fixture.componentInstance.canSend).toBeFalse();

    httpMock.expectOne(`${environment.apiBaseUrl}/api/v1/llm/chat`).flush({
      response: 'DI is...',
      model: 'phi3:mini',
      provider: 'ollama',
      duration_ms: 10,
    });
  });

  it('renders the response on success', () => {
    const fixture = TestBed.createComponent(LlmPlaygroundComponent);
    fixture.detectChanges();
    setMessage(fixture, 'Explain DI');
    fixture.componentInstance.send();

    httpMock.expectOne(`${environment.apiBaseUrl}/api/v1/llm/chat`).flush({
      response: 'DI is...',
      model: 'phi3:mini',
      provider: 'ollama',
      duration_ms: 10,
    });
    fixture.detectChanges();

    expect(fixture.componentInstance.result?.response).toBe('DI is...');
    expect(fixture.componentInstance.loading).toBeFalse();
    expect(fixture.componentInstance.errorMessage).toBeNull();
  });

  it('shows an error message when the request fails', () => {
    const fixture = TestBed.createComponent(LlmPlaygroundComponent);
    fixture.detectChanges();
    setMessage(fixture, 'Explain DI');
    fixture.componentInstance.send();

    httpMock.expectOne(`${environment.apiBaseUrl}/api/v1/llm/chat`).flush(
      { error: { code: 'LLMUnavailableError', message: 'could not connect to ollama' } },
      { status: 503, statusText: 'Service Unavailable' },
    );
    fixture.detectChanges();

    expect(fixture.componentInstance.errorMessage).toBe('could not connect to ollama');
    expect(fixture.componentInstance.loading).toBeFalse();
    expect(fixture.componentInstance.result).toBeNull();
  });
});
