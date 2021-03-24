import { Injectable } from '@angular/core';
import { Observable, from } from 'rxjs';
import { SearchQuery } from './results.service';
import { switchMap, delay, tap } from 'rxjs/operators';
import { ResultsJson } from './results-page/results.types';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';

//const httpHeaders = { 'Content-Type': 'application/json; charset=UTF-8' };

@Injectable({
  providedIn: 'root'
})
export class QueryService {

  //private static readonly headers = new HttpHeaders(httpHeaders);

  constructor(private http: HttpClient) { }

  /**
   * Create an observable pipeline from an input to a result or loading indicator. Returns an
   * observable that contains the raw results data received from the backend, in JSON format. 
   */
  getSearchData(input: Observable<SearchQuery>): Observable<ResultsJson> {
    console.log("getSearchData")
    return input.pipe(
      delay(250),  // debounce; can't use debounceTime because this observable only triggers once
      switchMap((q) => this.fetchSearch(q))
    );
  }

  /**
   * Makes a GET request to /search, and returns a JSON response. 
   */
  fetchSearch(query: SearchQuery): Observable<any> {
    console.log("searching")
    let params = new HttpParams();
    if (query.query) params.append("query", query.query);
    if (query.categories) params.append("categories", this.makeStringFromList(query.categories));
    if (query.journals) params.append("journals", this.makeStringFromList(query.journals));
    if (query.pubyears) params.append("pubyears", this.makeStringFromList(query.pubyears));
    params.append("type", query.type);
    params.append("deep", query.deep.toString());
    return this.http.get(
        'http://127.0.0.1' + '/search',
        { params: params }
      );
  }

  makeStringFromList(list: any[]) {
    return "[" + list.join() + "]";
  }

}
