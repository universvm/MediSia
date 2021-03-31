import { Component, OnInit, Inject } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatSelectionListChange } from '@angular/material/list';
import { SearchData } from 'src/app/search-page/search-page.component';
import { ResultsService } from 'src/app/results.service';
import { SearchService } from 'src/app/search.service';

@Component({
  selector: 'app-journal-filter-modal',
  templateUrl: './journal-filter-modal.component.html',
  styleUrls: ['./journal-filter-modal.component.scss']
})
export class JournalFilterModalComponent implements OnInit {
  journals: string[];
  searchData: SearchData | null;
  includedJournals: string[] = [];
  originalJournals: string[] = [];

  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    private resultsService: ResultsService,
    private searchService: SearchService,
  ) { 
    this.journals = [...this.resultsService.journals].slice(0,10);
    this.searchData = this.searchService.searchData;
    if (this.searchService.searchData) {
      this.includedJournals = this.searchService.searchData.journals ? this.makeListFromString(this.searchService.searchData.journals) : [];
      this.originalJournals = this.searchService.searchData.journals ? this.makeListFromString(this.searchService.searchData.journals) : [];
    }
  }

  makeListFromString(journals: string) {
    if (journals.includes(',')) {
      return journals.split(',').map(journal => journal.trim());
    } else return [journals];
  }

  check(journal: string) {
    return this.includedJournals.includes(journal);
  }

  ngOnInit() { }

  ngOnDestroy() { }

  onSelChange(event: MatSelectionListChange) {
    const includedJournals = new Set(event.source.options.filter(o => o.selected).map(o => o.value));
    this.searchService.searchData!.journals = [...includedJournals].join();
    this.includedJournals = this.searchService.searchData!.journals ? this.makeListFromString(this.searchService.searchData!.journals) : [];
    console.log(this.searchService.searchData!.journals);
  }

  applyFilters() {
    console.log(this.searchService.searchData);
    this.resultsService.updateQuery({
      journals: this.searchService.searchData!.journals,
      type: "follow-up",
      propagate: true,
    });
  }

  cancelFilters() {
    this.searchService.searchData!.journals = this.originalJournals.join();
    console.log(this.searchService.searchData!.journals);
  }

}
