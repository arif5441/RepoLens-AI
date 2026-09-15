import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import {
  ActivatedRoute,
  NavigationEnd,
  Router,
  RouterLink,
  RouterLinkActive,
  RouterOutlet,
} from '@angular/router';
import { filter, map, mergeMap } from 'rxjs/operators';

import { HealthService } from './core/services/health.service';

type SystemStatus = 'checking' | 'ok' | 'degraded' | 'error';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, CommonModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
})
export class AppComponent implements OnInit {
  pageTitle = 'Home';
  systemStatus: SystemStatus = 'checking';

  constructor(
    private readonly router: Router,
    private readonly activatedRoute: ActivatedRoute,
    private readonly healthService: HealthService,
  ) {}

  ngOnInit(): void {
    this.router.events
      .pipe(
        filter((event) => event instanceof NavigationEnd),
        map(() => {
          let route = this.activatedRoute;
          while (route.firstChild) {
            route = route.firstChild;
          }
          return route;
        }),
        mergeMap((route) => route.data),
      )
      .subscribe((data) => {
        this.pageTitle = (data['title'] as string) ?? 'RepoLens AI';
      });

    this.healthService.getHealth().subscribe({
      next: (health) => {
        this.systemStatus = health.status === 'ok' ? 'ok' : 'degraded';
      },
      error: () => {
        this.systemStatus = 'error';
      },
    });
  }

  get systemStatusLabel(): string {
    switch (this.systemStatus) {
      case 'ok':
        return 'All systems operational';
      case 'degraded':
        return 'Degraded — check status';
      case 'error':
        return 'Cannot reach API';
      default:
        return 'Checking status…';
    }
  }

  get systemStatusDotClass(): string {
    switch (this.systemStatus) {
      case 'ok':
        return 'bg-emerald-500';
      case 'degraded':
        return 'bg-amber-500';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-slate-300';
    }
  }
}
