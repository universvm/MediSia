import { Injectable } from '@angular/core';
import { Observable, from } from 'rxjs';
import { SearchQuery } from './results.service';
import { switchMap, delay, tap } from 'rxjs/operators';
import { ResultsJson } from './results-page/results.types';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';

//const httpHeaders = new HttpHeaders({
  //'Content-Type': 'application/json',
  //'Accept': 'application/json',
  //'Access-Control-Allow-Origin': '*',
//});

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
    let params = "";
    console.log("query " + query)
    if (query.query) {
      params = params + "?query=" + query.query;
    }
    if (query.categories) {
      params = params + "&categories=" + "[" + this.makeStringListFromString(query.categories) + "]";
    }
    if (query.journals) {
      params = params + "&journals=" + "[" + this.makeStringListFromString(query.journals) + "]";
    }
    if (query.pubyears) {
      params = params + "&pubyears=" + this.makeStringFromRange(query.pubyears);
    }
    params = params + "&type=" + query.type;
    params = params + "&deep=" + this.makeStringFromBool(query.deep);
    console.log("params " + params)
    return this.http.get(
        'http://127.0.0.1:8000' + '/search' + params,
      );
  }

  makeStringListFromString(list: string) {
    if (list.includes(',')) {
      let items = list.split(',');
      return items.map(item => {return "\"" + item.trim() + "\""}).join();
    } else return "\"" + list + "\"";
  }

  makeStringFromBool(bool: boolean) {
    if (bool === true) return "True";
    else return "False";
  }

  makeStringFromRange(range: string) {
    if (range.includes('-')) {
      let options = range.split('-');
      return "[" + options[0] + ',' + options[1] + ']';
    }
    return "[" + range + ",None" + ']';
  }

}
