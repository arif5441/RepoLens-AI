import { CommonModule } from '@angular/common';
import { Component, CUSTOM_ELEMENTS_SCHEMA, OnInit } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { Router } from '@angular/router';

import { IndexedRepositorySummary, IndexResponse } from '../../core/models/repository.model';
import { RepositoryService } from '../../core/services/repository.service';

@Component({
  selector: 'app-repository-management',
  standalone: true,
  imports: [CommonModule],
  schemas: [CUSTOM_ELEMENTS_SCHEMA],
  templateUrl: './repository-management.component.html',
})
export class RepositoryManagementComponent implements OnInit {
  repositories: IndexedRepositorySummary[] = [];
  listLoading = false;
  listError: string | null = null;

  url = 'https://github.com/trekhleb/learn-python';
  indexing = false;
  indexError: string | null = null;
  indexResult: IndexResponse | null = null;

  constructor(
    private readonly repositoryService: RepositoryService,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    this.loadRepositories();
  }

  get canIndex(): boolean {
    return !this.indexing && this.url.trim().length > 0;
  }

  onUrlChange(event: Event): void {
    this.url = (event.target as HTMLInputElement).value;
  }

  loadRepositories(): void {
    this.listLoading = true;
    this.listError = null;
    this.repositoryService.list().subscribe({
      next: (response) => {
        this.repositories = response.repositories;
        this.listLoading = false;
      },
      error: (err: HttpErrorResponse) => {
        this.listError = err.error?.error?.message ?? 'Could not load indexed repositories.';
        this.listLoading = false;
      },
    });
  }

  indexRepository(): void {
    if (!this.canIndex) {
      return;
    }

    this.indexing = true;
    this.indexError = null;
    this.indexResult = null;

    this.repositoryService.index(this.url.trim()).subscribe({
      next: (response) => {
        this.indexResult = response;
        this.indexing = false;
        this.loadRepositories();
      },
      error: (err: HttpErrorResponse) => {
        this.indexError = err.error?.error?.message ?? 'Could not index the repository.';
        this.indexing = false;
      },
    });
  }

  openChat(repository: string): void {
    this.router.navigate(['/chat'], { queryParams: { repository } });
  }
}
