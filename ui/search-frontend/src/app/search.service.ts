import { Injectable } from '@angular/core';
import { SearchData } from './search-page/search-page.component';

@Injectable({
  providedIn: 'root'
})
export class SearchService {
  searchData: SearchData | null = null;
  topics: Set<string> = new Set(['medicine', 'botany', 'immunology']);
  journals: Set<string> = new Set(['journal1','journal2','journal3','journal4','journal5']);
  authors: Set<string> = new Set();
  pubyears: Set<number> = new Set([2017, 2019, 2020]);

  constructor() { }
}
