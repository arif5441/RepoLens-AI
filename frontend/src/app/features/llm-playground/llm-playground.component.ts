import { CommonModule } from '@angular/common';
import { Component, CUSTOM_ELEMENTS_SCHEMA, OnInit } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';

import { LLMChatResponse } from '../../core/models/llm.model';
import { LlmService } from '../../core/services/llm.service';

@Component({
  selector: 'app-llm-playground',
  standalone: true,
  imports: [CommonModule],
  schemas: [CUSTOM_ELEMENTS_SCHEMA],
  templateUrl: './llm-playground.component.html',
})
export class LlmPlaygroundComponent implements OnInit {
  message = '';
  systemPrompt = '';
  models: string[] = [];
  selectedModel = '';

  loading = false;
  errorMessage: string | null = null;
  result: LLMChatResponse | null = null;

  constructor(private readonly llmService: LlmService) {}

  ngOnInit(): void {
    this.llmService.listModels().subscribe({
      next: (response) => {
        this.models = response.models;
      },
      error: () => {
        this.models = [];
      },
    });
  }

  get canSend(): boolean {
    return !this.loading && this.message.trim().length > 0;
  }

  onMessageChange(event: Event): void {
    this.message = (event.target as HTMLTextAreaElement).value;
  }

  onSystemPromptChange(event: Event): void {
    this.systemPrompt = (event.target as HTMLTextAreaElement).value;
  }

  onModelChange(event: Event): void {
    this.selectedModel = (event.target as HTMLSelectElement).value;
  }

  send(): void {
    if (!this.canSend) {
      return;
    }

    this.loading = true;
    this.errorMessage = null;
    this.result = null;

    this.llmService.chat(this.message.trim(), this.systemPrompt, this.selectedModel).subscribe({
      next: (response) => {
        this.result = response;
        this.loading = false;
      },
      error: (err: HttpErrorResponse) => {
        this.errorMessage = err.error?.error?.message ?? 'Could not reach the LLM. Please try again.';
        this.loading = false;
      },
    });
  }
}
