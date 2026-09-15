import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';

import { HealthResponse } from '../../core/models/health.model';
import { IndexedRepositorySummary } from '../../core/models/repository.model';
import { HealthService } from '../../core/services/health.service';
import { RepositoryService } from '../../core/services/repository.service';

interface FeatureCard {
  icon: 'ingest' | 'search' | 'chat' | 'citation' | 'playground';
  title: string;
  description: string;
  link: string;
}

const FEATURE_CARDS: FeatureCard[] = [
  {
    icon: 'ingest',
    title: 'GitHub Ingestion',
    description: 'Load a public repository — no clone, GitHub API only.',
    link: '/repositories',
  },
  {
    icon: 'search',
    title: 'Semantic Search',
    description: 'Find relevant code using local embeddings, not keyword match.',
    link: '/embeddings',
  },
  {
    icon: 'chat',
    title: 'RAG Chat',
    description: 'Ask questions and get answers grounded in retrieved code.',
    link: '/chat',
  },
  {
    icon: 'citation',
    title: 'Source Citations',
    description: 'Every answer links back to the exact file and line range.',
    link: '/chat',
  },
  {
    icon: 'playground',
    title: 'LLM Playground',
    description: 'Raw model chat, no repository context — for diagnostics.',
    link: '/playground',
  },
];

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './dashboard.component.html',
})
export class DashboardComponent implements OnInit {
  health: HealthResponse | null = null;
  healthLoading = true;
  healthError = false;

  repositories: IndexedRepositorySummary[] = [];
  repositoriesLoading = true;
  repositoriesError = false;

  readonly featureCards = FEATURE_CARDS;

  constructor(
    private readonly healthService: HealthService,
    private readonly repositoryService: RepositoryService,
  ) {}

  ngOnInit(): void {
    this.healthService.getHealth().subscribe({
      next: (health) => {
        this.health = health;
        this.healthLoading = false;
      },
      error: () => {
        this.healthError = true;
        this.healthLoading = false;
      },
    });

    this.repositoryService.list().subscribe({
      next: (response) => {
        this.repositories = [...response.repositories]
          .sort((a, b) => Date.parse(b.last_indexed_at) - Date.parse(a.last_indexed_at))
          .slice(0, 5);
        this.repositoriesLoading = false;
      },
      error: () => {
        this.repositoriesError = true;
        this.repositoriesLoading = false;
      },
    });
  }

  relativeTime(isoDate: string): string {
    const diffMs = Date.now() - Date.parse(isoDate);
    if (Number.isNaN(diffMs)) {
      return isoDate;
    }
    const minutes = Math.floor(diffMs / 60000);
    if (minutes < 1) return 'just now';
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  }
}
