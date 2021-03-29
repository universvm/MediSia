import { Injectable } from '@angular/core';
import { SearchData } from './search-page/search-page.component';
import { BehaviorSubject, Observable, Subject } from 'rxjs';
import { ResultsJson } from './results-page/results.types';
import { QueryService } from './query.service';
import { tap, filter } from 'rxjs/operators';
import { SearchService } from './search.service';

export interface SearchQuery {
  readonly query: string | null;
  readonly categories: string | null;
  //readonly author: string[] | null;
  readonly journals: string | null;
  readonly pubyears: string | null;
  readonly deep: boolean;
  readonly type: "new" | "follow-up";
  readonly propagate: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class ResultsService {
  //searchData: SearchData | null = null;
  categories: Set<string> = new Set(['medicine', 'botany', 'immunology']);
  journals: Set<string> = new Set(['journal1','journal2','journal3','journal4','journal5']);
  //authors: Set<string> = new Set();
  pubyears: Set<number> = new Set([2017, 2019, 2020]);

  /**
   * Default state of the search query when the user lands on the /results page
   */
  public static readonly defaultSearchQuery: SearchQuery = {
    query: null,
    categories: null,
    journals: null,
    pubyears: null,
    deep: false,
    type: "new",
    propagate: false,
  } as const;

  /**
   * Subject representing the current state of the SearchQuery
   */
  private query$ = new BehaviorSubject<SearchQuery>(ResultsService.defaultSearchQuery);

  /**
   * Public observable for components to subscribe to
   * This is used to obtain the results from a query made to the backend
   */
  public result$: Observable<ResultsJson>;

  constructor(private queryService: QueryService, private searchService: SearchService) {
    const result$ = new Subject<ResultsJson>();
    this.query$.pipe(
      filter((q): q is SearchQuery => q !== null && q.propagate),
      this.queryService.getSearchData.bind(this.queryService),
      tap((parsed: ResultsJson) => {
        this.journals = new Set(parsed.journals);
        this.pubyears = new Set(parsed.pubyears);
        this.categories = new Set(parsed.categories);
        this.updateQuery({
          type: "follow-up",
          propagate: false,
        });
      }),
    ).subscribe(result$);
    this.result$ = result$;
  }

  /**
   * Fetches the result with the updated search query without actually modifying the search query.
   */
  public async fetchResult(update: Partial<SearchQuery>): Promise<ResultsJson> {
    return await this.queryService.fetchSearch({
      ...this.getCurrentQuery(),
      ...update,
    }).toPromise();
  }

  /**
   * Resets the query to default state.
   * Used in flight-page's ngOnInit to handle the case where the user navigates from /itinerary to /search
   */
  public reset() {
    this.query$.next(ResultsService.defaultSearchQuery);
  }

  /**
   * Replaces the current query with the given one.
   */
  public setQuery(query: SearchQuery) {
    this.query$.next(query);
  }

  /**
   * Partially replaces the current search query with a new search query
   * The new search query will consist of fields of the old search query overwritten by all fields
   * in the given partial search query.
   */
  public updateQuery(update: Partial<SearchQuery>) {
    this.setQuery({
      ...this.getCurrentQuery(),
      ...update,
    });
  }

  /**
   * Returns an observable for query. If the current query values are needed, use getCurrentQuery() instead
   */
  public getQuery(): Observable<SearchQuery> {
    return this.query$.pipe(
      filter((a): a is SearchQuery => a !== null),
    );
  }


  /**
   * Returns the latest values in the query$ subject
   */
  public getCurrentQuery(): SearchQuery {
    return this.query$.getValue();
  }
}
