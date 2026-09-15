import { CommonModule } from '@angular/common';
import { Component, CUSTOM_ELEMENTS_SCHEMA, OnInit } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { ActivatedRoute } from '@angular/router';

import { AskResponse, IndexedRepositorySummary } from '../../core/models/repository.model';
import { RepositoryService } from '../../core/services/repository.service';

interface ConversationTurn {
  question: string;
  response: AskResponse | null;
  error: string | null;
  expandedCitation: number | null;
}

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule],
  schemas: [CUSTOM_ELEMENTS_SCHEMA],
  templateUrl: './chat.component.html',
})
export class ChatComponent implements OnInit {
  repositories: IndexedRepositorySummary[] = [];
  repositoriesLoading = false;
  selectedRepository = '';

  question = '';
  asking = false;
  turns: ConversationTurn[] = [];

  constructor(
    private readonly repositoryService: RepositoryService,
    private readonly route: ActivatedRoute,
  ) {}

  ngOnInit(): void {
    const fromQuery = this.route.snapshot.queryParamMap.get('repository');
    if (fromQuery) {
      this.selectedRepository = fromQuery;
    }

    this.repositoriesLoading = true;
    this.repositoryService.list().subscribe({
      next: (response) => {
        this.repositories = response.repositories;
        if (!this.selectedRepository && response.repositories.length > 0) {
          this.selectedRepository = response.repositories[0].repository;
        }
        this.repositoriesLoading = false;
      },
      error: () => {
        this.repositoriesLoading = false;
      },
    });
  }

  get canAsk(): boolean {
    return !this.asking && this.selectedRepository.length > 0 && this.question.trim().length > 0;
  }

  onRepositoryChange(event: Event): void {
    this.selectedRepository = (event.target as HTMLSelectElement).value;
  }

  onQuestionChange(event: Event): void {
    this.question = (event.target as HTMLTextAreaElement).value;
  }

  toggleCitation(turn: ConversationTurn, index: number): void {
    turn.expandedCitation = turn.expandedCitation === index ? null : index;
  }

  ask(): void {
    if (!this.canAsk) {
      return;
    }

    const question = this.question.trim();
    const turn: ConversationTurn = { question, response: null, error: null, expandedCitation: null };
    this.turns = [turn, ...this.turns];
    this.question = '';
    this.asking = true;

    this.repositoryService.ask(this.selectedRepository, question).subscribe({
      next: (response) => {
        turn.response = response;
        this.asking = false;
      },
      error: (err: HttpErrorResponse) => {
        turn.error = err.error?.error?.message ?? 'Could not get an answer. Please try again.';
        this.asking = false;
      },
    });
  }
}
