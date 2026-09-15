import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';

import { HealthResponse } from '../../core/models/health.model';
import { HealthService } from '../../core/services/health.service';
import { StatusIndicatorComponent } from '../../shared/components/status-indicator/status-indicator.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, StatusIndicatorComponent],
  templateUrl: './dashboard.component.html',
})
export class DashboardComponent implements OnInit {
  health: HealthResponse | null = null;
  loading = true;
  loadError = false;

  constructor(private readonly healthService: HealthService) {}

  ngOnInit(): void {
    this.healthService.getHealth().subscribe({
      next: (health) => {
        this.health = health;
        this.loading = false;
      },
      error: () => {
        this.loadError = true;
        this.loading = false;
      },
    });
  }
}
