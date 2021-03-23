import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TopicFilterModalComponent } from './topic-filter-modal.component';

describe('TopicFilterModalComponent', () => {
  let component: TopicFilterModalComponent;
  let fixture: ComponentFixture<TopicFilterModalComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ TopicFilterModalComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(TopicFilterModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
