import jsonlines


def select_and_save_biopapers(unpaywall_path, output_path, journals_to_include):
    with jsonlines.open('unpaywall_snapshot_2020-10-09T153852.jsonl') as reader:
        with jsonlines.open('output.jsonl', mode='a') as writer:
            for i, obj in enumerate(reader):
                pprint.pprint(obj)
                if obj['journal_name'] == 'Law and Contemporary Problems':
                    writer.write(obj)
                if i == 4:
                    break