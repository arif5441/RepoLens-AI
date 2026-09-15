import { CommonModule } from '@angular/common';
import { Component, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';

import { IngestionResponse } from '../../core/models/ingestion.model';
import { IngestionService } from '../../core/services/ingestion.service';

@Component({
  selector: 'app-repository-ingestion',
  standalone: true,
  imports: [CommonModule],
  schemas: [CUSTOM_ELEMENTS_SCHEMA],
  templateUrl: './repository-ingestion.component.html',
})
export class RepositoryIngestionComponent {
  url = 'https://github.com/octocat/Spoon-Knife';
  loading = false;
  errorMessage: string | null = null;
  result: IngestionResponse | null = null;

  constructor(private readonly ingestionService: IngestionService) {}

  get canIngest(): boolean {
    return !this.loading && this.url.trim().length > 0;
  }

  get skippedReasonEntries(): { reason: string; count: number }[] {
    if (!this.result) {
      return [];
    }
    return Object.entries(this.result.skipped_reasons)
      .map(([reason, count]) => ({ reason, count }))
      .sort((a, b) => b.count - a.count);
  }

  onUrlChange(event: Event): void {
    this.url = (event.target as HTMLInputElement).value;
  }

  ingest(): void {
    if (!this.canIngest) {
      return;
    }

    this.loading = true;
    this.errorMessage = null;
    this.result = null;

    this.ingestionService.ingest(this.url.trim()).subscribe({
      next: (response) => {
        this.result = response;
        this.loading = false;
      },
      error: (err: HttpErrorResponse) => {
        this.errorMessage = err.error?.error?.message ?? 'Could not ingest the repository. Please try again.';
        this.loading = false;
      },
    });
  }
}
