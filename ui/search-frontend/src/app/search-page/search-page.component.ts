import { Component, OnInit } from '@angular/core';
import { FormControl, FormGroup, AbstractControl, ValidationErrors, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { SearchService } from '../search.service';
import { Observable } from 'rxjs';
import {map, startWith} from 'rxjs/operators';
import { ResultsService } from '../results.service';

export interface SearchData {
  query: string | null;
  categories: string[] | null;
  //author: string[] | null;
  journals: string[] | null;
  pubyears: number[] | null;
  deep: boolean;
}

const options: string[] = ["agriculture", "anatomy", "biochemistry", "bioengineering", "bioinformatics",
                      "biology", "biophysics", "botany", "dental", "ecology", "entomology", "forestry",
                      "genetics", "healthcare", "medicine", "microbiology", "molecular", "mycology", 
                      "neuroscience", "nursing", "nutrition", "ornithology", "pharmacy", "psychiatry",
                      "virology", "zoology"];

@Component({
  selector: 'app-search-page',
  templateUrl: './search-page.component.html',
  styleUrls: ['./search-page.component.scss']
})
export class SearchPageComponent implements OnInit {
  filteredOptions: Observable<string[]> = new Observable;

  searchForm = new FormGroup({
    query: new FormControl(null, [Validators.required]),
    categories: new FormControl(null, [this.categoryValidator]),
    //author: new FormControl(null),
    journals: new FormControl(null),
    pubyears: new FormControl(null, [this.pubYearValidator]),
    deep: new FormControl(false),
  });

  isAdvanced: boolean = false;

  constructor(
    private router: Router,
    private searchService: SearchService,
    private resultsService: ResultsService,
  ) { }

  ngOnInit() {
    this.filteredOptions = this.searchForm.controls.categories.valueChanges
      .pipe(
        startWith(''),
        map(value => this._filter(value))
      );
  }

  private _filter(value: any): string[] {
    const filterValue = value.toLowerCase();
    return options.filter(option => option.toLowerCase().includes(filterValue));
  }

  onSubmit() {
    const value: SearchData = this.searchForm.value;
    // when sending to backend, atm if !isAdvanced, set those fields to null regardless of input
    if (!this.isAdvanced) {
      //value.author = null;
      value.categories = null;
      value.journals = null;
      value.pubyears = null;
    }
    this.searchService.searchData = value;
    this.resultsService.reset();
    this.resultsService.updateQuery({ 
      query: value.query,
      categories: value.categories,
      journals: value.journals,
      pubyears: value.pubyears,
      deep: value.deep,
      propagate: true 
    });
    this.router.navigate(['results']);
  }

  onAdvanced() {
    this.isAdvanced = !this.isAdvanced;
  }

  pubYearValidator(control: AbstractControl): ValidationErrors | null {
    const regex = RegExp(/^(\d){4}(( )?-( )?(\d){4})?( )?$/); //make regex handle year/rangeg
    const matches = regex.test(control.value);
    if (control.value === null || control.value === '') {
      return null;
    } else if (!matches) {
      return { invalidYear: true };
    } else {
      return null;
    }
  }

  categoryValidator(control: AbstractControl): ValidationErrors | null {
    if (control.value === null || control.value === "") return null;
    else if (!options.includes(control.value)) return { invalidCategory: true};
    else return null;
  }

}
