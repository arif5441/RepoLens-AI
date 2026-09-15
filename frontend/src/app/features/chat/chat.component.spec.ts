import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';

import { environment } from '../../../environments/environment';
import { ChatComponent } from './chat.component';

describe('ChatComponent', () => {
  let httpMock: HttpTestingController;

  async function setup(queryParams: Record<string, string> = {}) {
    await TestBed.configureTestingModule({
      imports: [ChatComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { queryParamMap: convertToParamMap(queryParams) } },
        },
      ],
    }).compileComponents();
    httpMock = TestBed.inject(HttpTestingController);
  }

  function flushRepositories(repositories: any[]) {
    httpMock.expectOne(`${environment.apiBaseUrl}/api/v1/repositories`).flush({ repositories });
  }

  it('preselects the repository from the query param', async () => {
    await setup({ repository: 'octocat/from-query' });
    const fixture = TestBed.createComponent(ChatComponent);
    fixture.detectChanges();
    flushRepositories([{ repository: 'octocat/other', chunk_count: 1, last_indexed_at: '2026-01-01' }]);

    expect(fixture.componentInstance.selectedRepository).toBe('octocat/from-query');
  });

  it('defaults to the first repository when none is preselected', async () => {
    await setup();
    const fixture = TestBed.createComponent(ChatComponent);
    fixture.detectChanges();
    flushRepositories([{ repository: 'octocat/demo', chunk_count: 1, last_indexed_at: '2026-01-01' }]);

    expect(fixture.componentInstance.selectedRepository).toBe('octocat/demo');
  });

  it('disables ask when the question is blank', async () => {
    await setup();
    const fixture = TestBed.createComponent(ChatComponent);
    fixture.detectChanges();
    flushRepositories([{ repository: 'octocat/demo', chunk_count: 1, last_indexed_at: '2026-01-01' }]);

    fixture.componentInstance.question = '   ';
    expect(fixture.componentInstance.canAsk).toBeFalse();
  });

  it('adds a turn and renders the answer with citations on success', async () => {
    await setup();
    const fixture = TestBed.createComponent(ChatComponent);
    fixture.detectChanges();
    flushRepositories([{ repository: 'octocat/demo', chunk_count: 1, last_indexed_at: '2026-01-01' }]);

    fixture.componentInstance.question = 'What does foo do?';
    fixture.componentInstance.ask();

    httpMock.expectOne(`${environment.apiBaseUrl}/api/v1/repositories/ask`).flush({
      repository: 'octocat/demo', question: 'What does foo do?', answer: 'It does X [1].',
      citations: [{ file_path: 'a.py', start_line: 1, end_line: 2, similarity: 0.9, content: 'def foo(): pass' }],
      grounded: true, model: 'phi3:mini', duration_ms: 100,
    });
    fixture.detectChanges();

    expect(fixture.componentInstance.turns.length).toBe(1);
    expect(fixture.componentInstance.turns[0].response?.answer).toBe('It does X [1].');
  });

  it('toggles citation expansion', async () => {
    await setup();
    const fixture = TestBed.createComponent(ChatComponent);
    fixture.detectChanges();
    flushRepositories([]);

    const turn = {
      question: 'q',
      response: null,
      error: null,
      expandedCitation: null as number | null,
      collapsed: false,
    };
    fixture.componentInstance.toggleCitation(turn, 0);
    expect(turn.expandedCitation).toBe(0);
    fixture.componentInstance.toggleCitation(turn, 0);
    expect(turn.expandedCitation).toBeNull();
  });

  it('collapses earlier turns when a new question is asked', async () => {
    await setup();
    const fixture = TestBed.createComponent(ChatComponent);
    fixture.detectChanges();
    flushRepositories([{ repository: 'octocat/demo', chunk_count: 1, last_indexed_at: '2026-01-01' }]);

    fixture.componentInstance.question = 'first question';
    fixture.componentInstance.ask();
    httpMock.expectOne(`${environment.apiBaseUrl}/api/v1/repositories/ask`).flush({
      repository: 'octocat/demo', question: 'first question', answer: 'answer one',
      citations: [], grounded: true, model: 'phi3:mini', duration_ms: 100,
    });

    fixture.componentInstance.question = 'second question';
    fixture.componentInstance.ask();
    httpMock.expectOne(`${environment.apiBaseUrl}/api/v1/repositories/ask`).flush({
      repository: 'octocat/demo', question: 'second question', answer: 'answer two',
      citations: [], grounded: true, model: 'phi3:mini', duration_ms: 100,
    });

    expect(fixture.componentInstance.turns[0].question).toBe('second question');
    expect(fixture.componentInstance.turns[0].collapsed).toBeFalse();
    expect(fixture.componentInstance.turns[1].question).toBe('first question');
    expect(fixture.componentInstance.turns[1].collapsed).toBeTrue();
  });

  it('selectTurn expands the chosen turn', async () => {
    await setup();
    const fixture = TestBed.createComponent(ChatComponent);
    fixture.detectChanges();
    flushRepositories([{ repository: 'octocat/demo', chunk_count: 1, last_indexed_at: '2026-01-01' }]);

    fixture.componentInstance.turns = [
      { question: 'q1', response: null, error: null, expandedCitation: null, collapsed: true },
    ];
    fixture.componentInstance.selectTurn(0);
    expect(fixture.componentInstance.turns[0].collapsed).toBeFalse();
  });
});
