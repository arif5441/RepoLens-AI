import { CommonModule } from '@angular/common';
import { Component, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';

import { EmbeddingTestResponse } from '../../core/models/embedding.model';
import { EmbeddingService } from '../../core/services/embedding.service';

@Component({
  selector: 'app-embeddings-playground',
  standalone: true,
  imports: [CommonModule],
  schemas: [CUSTOM_ELEMENTS_SCHEMA],
  templateUrl: './embeddings-playground.component.html',
})
export class EmbeddingsPlaygroundComponent {
  texts: string[] = [
    'calculate employee salary',
    'compute payroll amount',
    'weather forecast for tomorrow',
  ];

  loading = false;
  errorMessage: string | null = null;
  result: EmbeddingTestResponse | null = null;

  constructor(private readonly embeddingService: EmbeddingService) {}

  get nonBlankTexts(): string[] {
    return this.texts.map((t) => t.trim()).filter((t) => t.length > 0);
  }

  get canSend(): boolean {
    return !this.loading && this.nonBlankTexts.length >= 2;
  }

  get sortedSimilarities() {
    return this.result ? [...this.result.similarities].sort((a, b) => b.similarity - a.similarity) : [];
  }

  onTextChange(index: number, event: Event): void {
    this.texts[index] = (event.target as HTMLInputElement).value;
  }

  addText(): void {
    if (this.texts.length < 8) {
      this.texts.push('');
    }
  }

  removeText(index: number): void {
    if (this.texts.length > 2) {
      this.texts.splice(index, 1);
    }
  }

  send(): void {
    if (!this.canSend) {
      return;
    }

    this.loading = true;
    this.errorMessage = null;
    this.result = null;

    this.embeddingService.test(this.nonBlankTexts).subscribe({
      next: (response) => {
        this.result = response;
        this.loading = false;
      },
      error: (err: HttpErrorResponse) => {
        this.errorMessage = err.error?.error?.message ?? 'Could not generate embeddings. Please try again.';
        this.loading = false;
      },
    });
  }
}
