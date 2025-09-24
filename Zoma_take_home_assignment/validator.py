
import json, sys
from jsonschema import validate, Draft202012Validator

def main(plan_path='plan.json', schema_path='output_schema.json'):
    with open(schema_path) as f:
        schema = json.load(f)
    with open(plan_path) as f:
        plan = json.load(f)

    v = Draft202012Validator(schema)
    errors = sorted(v.iter_errors(plan), key=lambda e: e.path)
    if errors:
        print('❌ Schema validation failed:')
        for e in errors:
            loc = '/'.join([str(x) for x in e.absolute_path]) or '(root)'
            print(f' - {loc}: {e.message}')
        sys.exit(1)

    # Extra sanity checks
    ids = [p['id'] for p in plan['phases']]
    if len(ids) != len(set(ids)):
        print('❌ Duplicate phase IDs.')
        sys.exit(1)

    print('✅ Plan is valid.')
    return 0

if __name__ == '__main__':
    p = sys.argv[1] if len(sys.argv) > 1 else 'plan.json'
    s = sys.argv[2] if len(sys.argv) > 2 else 'output_schema.json'
    sys.exit(main(p, s))
