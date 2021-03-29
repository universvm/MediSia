import { Injectable } from '@angular/core';
import { SearchData } from './search-page/search-page.component';

@Injectable({
  providedIn: 'root'
})
export class SearchService {
  searchData: SearchData | null = null;
}
