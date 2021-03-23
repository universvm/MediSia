import { Component, OnInit } from '@angular/core';
import { FormControl, FormGroup, AbstractControl, ValidationErrors, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { SearchService } from '../search.service';
import { Observable } from 'rxjs';
import {map, startWith} from 'rxjs/operators';

export interface SearchData {
  query: string | null;
  category: string[] | null;
  author: string[] | null;
  journal: string[] | null;
  pubyear: number[] | null;
  deepSearch: boolean;
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
    category: new FormControl(null, [this.categoryValidator]),
    author: new FormControl(null),
    journal: new FormControl(null),
    pubyear: new FormControl(null, [this.pubYearValidator]),
    deepSearch: new FormControl(false),
  });

  isAdvanced: boolean = false;
  isDeep: boolean = false;

  constructor(
    private router: Router,
    private searchService: SearchService,
  ) { }

  ngOnInit() {
    this.filteredOptions = this.searchForm.controls.category.valueChanges
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

    console.log(value.query);
    console.log(value.category);
    console.log(value.author);
    console.log(value.journal);
    console.log(value.pubyear);
    console.log(value.deepSearch);

    // when sending to backend, atm if !isAdvanced, set those fields to null regardless of input
    this.searchService.searchData = value;
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
