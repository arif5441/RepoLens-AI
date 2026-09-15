import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';

import { ComponentStatusValue } from '../../../core/models/health.model';

@Component({
  selector: 'app-status-indicator',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './status-indicator.component.html',
})
export class StatusIndicatorComponent {
  @Input({ required: true }) label!: string;
  @Input({ required: true }) status!: ComponentStatusValue | 'checking';
  @Input() detail: string | null = null;

  get statusText(): string {
    switch (this.status) {
      case 'ok':
        return 'Connected';
      case 'error':
        return 'Error';
      case 'unavailable':
        return 'Unavailable';
      default:
        return 'Checking…';
    }
  }

  get dotClass(): string {
    switch (this.status) {
      case 'ok':
        return 'bg-emerald-500';
      case 'error':
        return 'bg-red-500';
      case 'unavailable':
        return 'bg-amber-500';
      default:
        return 'bg-slate-300';
    }
  }
}
