import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { SearchPageComponent } from './search-page/search-page.component';
import { ResultsPageComponent } from './results-page/results-page.component';

const routes: Routes = [
  { path: 'search', component: SearchPageComponent },
  { path: 'results', component: ResultsPageComponent },
  { path: '**', redirectTo: '/search' },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
