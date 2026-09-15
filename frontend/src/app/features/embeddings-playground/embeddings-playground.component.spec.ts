import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';

import { environment } from '../../../environments/environment';
import { EmbeddingsPlaygroundComponent } from './embeddings-playground.component';

describe('EmbeddingsPlaygroundComponent', () => {
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [EmbeddingsPlaygroundComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    httpMock = TestBed.inject(HttpTestingController);
  });

  it('starts with two default example texts and send enabled', () => {
    const fixture = TestBed.createComponent(EmbeddingsPlaygroundComponent);
    fixture.detectChanges();
    expect(fixture.componentInstance.canSend).toBeTrue();
  });

  it('disables send when fewer than two non-blank texts remain', () => {
    const fixture = TestBed.createComponent(EmbeddingsPlaygroundComponent);
    fixture.detectChanges();
    fixture.componentInstance.texts = ['only one', ''];
    expect(fixture.componentInstance.canSend).toBeFalse();
  });

  it('adds and removes text rows, never dropping below two', () => {
    const fixture = TestBed.createComponent(EmbeddingsPlaygroundComponent);
    fixture.detectChanges();
    const instance = fixture.componentInstance;
    const startCount = instance.texts.length;

    instance.addText();
    expect(instance.texts.length).toBe(startCount + 1);

    instance.removeText(0);
    instance.removeText(0);
    instance.removeText(0);
    expect(instance.texts.length).toBeGreaterThanOrEqual(2);
  });

  it('renders similarity results on success', () => {
    const fixture = TestBed.createComponent(EmbeddingsPlaygroundComponent);
    fixture.detectChanges();
    fixture.componentInstance.send();

    httpMock.expectOne(`${environment.apiBaseUrl}/api/v1/embeddings/test`).flush({
      model: 'sentence-transformers/all-MiniLM-L6-v2',
      dimension: 384,
      count: 3,
      embeddings: [[0.1], [0.2], [0.3]],
      similarities: [
        { text_a_index: 0, text_b_index: 1, text_a: 'a', text_b: 'b', similarity: 0.8 },
        { text_a_index: 0, text_b_index: 2, text_a: 'a', text_b: 'c', similarity: 0.1 },
        { text_a_index: 1, text_b_index: 2, text_a: 'b', text_b: 'c', similarity: 0.05 },
      ],
      duration_ms: 12,
    });
    fixture.detectChanges();

    expect(fixture.componentInstance.result?.count).toBe(3);
    expect(fixture.componentInstance.sortedSimilarities[0].similarity).toBe(0.8);
    expect(fixture.componentInstance.loading).toBeFalse();
  });

  it('shows an error message when the request fails', () => {
    const fixture = TestBed.createComponent(EmbeddingsPlaygroundComponent);
    fixture.detectChanges();
    fixture.componentInstance.send();

    httpMock.expectOne(`${environment.apiBaseUrl}/api/v1/embeddings/test`).flush(
      { error: { code: 'EmbeddingModelUnavailableError', message: 'embedding model unavailable' } },
      { status: 503, statusText: 'Service Unavailable' },
    );
    fixture.detectChanges();

    expect(fixture.componentInstance.errorMessage).toBe('embedding model unavailable');
    expect(fixture.componentInstance.result).toBeNull();
  });
});
