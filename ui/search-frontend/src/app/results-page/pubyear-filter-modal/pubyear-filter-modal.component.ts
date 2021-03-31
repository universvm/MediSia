import { Component, OnInit, Inject } from '@angular/core';
import { SearchData } from 'src/app/search-page/search-page.component';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatSelectionListChange } from '@angular/material/list';
import { ResultsService } from 'src/app/results.service';
import { SearchService } from 'src/app/search.service';

@Component({
  selector: 'app-pubyear-filter-modal',
  templateUrl: './pubyear-filter-modal.component.html',
  styleUrls: ['./pubyear-filter-modal.component.scss']
})
export class PubyearFilterModalComponent implements OnInit {
  years: number[];
  searchData: SearchData | null;
  includedYears: string[] = [];
  originalYears: string[] = [];

  constructor(
    @Inject(MAT_DIALOG_DATA) public data: string[],
    private resultsService: ResultsService,
    private searchService: SearchService,
  ) { 
    this.years = [...this.resultsService.pubyears].slice(0, 10).sort(function(a, b){return b-a});;
    this.searchData = this.searchService.searchData;
    if (this.searchService.searchData) {
      this.includedYears = this.searchService.searchData.pubyears ? this.makeListFromString(this.searchService.searchData.pubyears) : [];
      this.originalYears = this.searchService.searchData.pubyears ? this.makeListFromString(this.searchService.searchData.pubyears) : [];
    }
  }

  makeListFromString(journals: string) {
    if (journals.includes(',')) {
      return journals.split(',');
    } else return [journals];
  }

  ngOnInit() { }

  ngOnDestroy() { }

  onSelChange(event: MatSelectionListChange) {
    const includedYears = new Set(event.source.options.filter(o => o.selected).map(o => o.value));
    this.searchService.searchData!.pubyears = [...includedYears].join();
    this.includedYears = this.searchService.searchData!.pubyears ? this.makeListFromString(this.searchService.searchData!.pubyears) : [];
    console.log(this.searchService.searchData!.pubyears);
  }

  applyFilters() {
    console.log(this.searchService.searchData);
    this.resultsService.updateQuery({
      pubyears: this.searchService.searchData!.pubyears,
      type: "follow-up",
      propagate: true,
    });
  }

  cancelFilters() {
    this.searchService.searchData!.pubyears = this.originalYears.join();
    console.log(this.searchService.searchData!.pubyears);
  }

}
