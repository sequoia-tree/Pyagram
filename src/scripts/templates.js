function compile(template) {
    return Handlebars.compile(template, {
        noEscape: true,
        assumeObjects: true,
    });
}

export const PYAGRAM_TEMPLATE = compile(`
<div class="overlap-wrapper">
  <table class="overlap border-collapse font-family-monospace" id="pyagram-state-table">
    <tr>
      <td class="align-top">
        {{decodeFrameSnapshot global_frame}}
      </td>
      <td class="align-top pl-5">
        {{#each memory_state}}
          TODO
        {{/each}}
      </td>
    </tr>
  </table>
  <svg class="overlap" id="pyagram-svg-canvas" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <marker id="circle" markerWidth="6.5" markerHeight="6.5" refX="5" refY="5">
        <circle cx="5" cy="5" r="1.5" fill="black"/>
      </marker>
      <marker id="arrowhead" markerWidth="6" markerHeight="6" refX="3" refY="5" viewBox="0 0 10 10" orient="auto">
        <path d="M0,0 L10,5 0,10 Z"/>
      </marker>
    </defs>
    <g id="pointers" fill="none" stroke="black" stroke-width="1.5" marker-start="url(#circle)" marker-end="url(#arrowhead)"/>
  </svg>
</div>
`)

export const ELEMENT_TEMPLATE = compile(`
{{#each flags}}
  {{decodeFlagSnapshot this}}
{{/each}}
`)

export const FLAG_TEMPLATE = compile(`
<div class="pyagram-flag m-3">
  <div class="pyagram-banner {{#if is_curr_element}} curr-element {{/if}}">
    <table class="text-center">
      <tr>
        {{#each banner}}
          <td {{#unless (isEmpty bindings)}} colspan="{{sum (mul 2 bindings.length) -1}}" {{/unless}}>
            {{code}}
          </td>
        {{/each}}
      </tr>
      <tr>
        {{#each banner}}
          {{#if (isEmpty bindings)}}
            {{#if (isEqual @index 1)}}
              {{#if @last}}
                <td class="text-left">()</td>
              {{else}}
                <td class="text-left">(</td>
              {{/if}}
            {{else if @last}}
              <td class="text-right">)</td>
            {{else}}
              <td class="text-left">,</td>
            {{/if}}
          {{else}}
            {{#each bindings}}
              <td class="pyagram-value {{#if (isNull this)}} pyagram-placeholder {{/if}}">
                {{#if (isNull this)}}
                  -
                {{else}}
                  {{decodeReferenceSnapshot this}}
                {{/if}}
              </td>
              {{#unless @last}}
                <td>,</td>
              {{/unless}}
            {{/each}}
          {{/if}}
        {{/each}}
      </tr>
    </table>
  </div>
  {{decodeElementSnapshot this}}
  {{#if (isNull frame)}}
    <div class="pyagram-placeholder">
      -
    </div>
  {{else}}
    {{decodeFrameSnapshot frame}}
  {{/if}}
</div>
`)

// TODO: Display the parent(s) too. Put the logic in the if/elif/elif/else cases.
// TODO: Verify this works with classes, instances, and generators (with `yield` + `yield from`).
// TODO: Replace {{key}} with {{decodeBindingSnapshot key}}. In 99.99% of cases the key should be a string; a variable `'var'` should show up as `var`. If it ain't a string, handle it like a ref. (This will require slight modification to encode.py based on the is_bindings parameter.)
export const FRAME_TEMPLATE = compile(`
<div class="pyagram-frame {{#if (isEqual type 'function')}} mx-3 {{else}} mr-3 {{/if}} my-3 {{#if is_curr_element}} curr-element {{/if}}">
  <div class="pyagram-frame-name">
    {{#if (isEqual type 'function')}}
      <span class="font-family-sans-serif">{{name}}</span>
    {{else if (isEqual type 'generator')}}
      <span class="font-family-sans-serif">generator </span>{{name}}
    {{else if (isEqual type 'class')}}
      <span class="font-family-sans-serif">class </span>{{name}}
    {{else if (isEqual type 'instance')}}
      {{name}}<span class="font-family-sans-serif"> instance</span>
    {{/if}}
  </div>
  <table class="ml-auto mr-0">
    {{#each bindings}}
      <tr>
        <td class="text-right">
          {{key}}
        </td>
        <td class="text-left pyagram-value" {{#unless (isNull ../from)}} colspan="3" {{/unless}}>
          {{decodeReferenceSnapshot value}}
        </td>
      </tr>
    {{/each}}
    {{#unless (isNull return_value)}}
      <tr>
        <td class="text-right font-family-sans-serif">
          {{#if (isEqual type 'generator')}}
            Yield value
          {{else}}
            Return value
          {{/if}}
        </td>
        <td class="text-left pyagram-value">
          {{decodeReferenceSnapshot return_value}}
        </td>
        {{#unless (isNull from)}}
          <td class="text-left font-family-sans-serif">
            from
          </td>
          <td class="text-left pyagram-value">
            {{decodeReferenceSnapshot from}}
          </td>
        {{/unless}}
      </tr>
    {{/unless}}
  </table>
</div>
{{decodeElementSnapshot this}}
`)

export const UNKNOWN_VALUE_TEMPLATE = compile(`
<span class="pyagram-unknown">
  (?)
</span>
`)

export const PRIMITIVE_TEMPLATE = compile(`
{{this}}
`)

export const REFERENT_TEMPLATE = compile(`
<span class="pyagram-placeholder pyagram-reference reference-{{this}}">
  -
</span>
`)

// OBJECT_TEMPLATE = """
// <div id="object-{{ id }}" class="pyagram-object m-3">
//   {{ get_object_body_html(object) }}
// </div>
// """

// FUNCTION_TEMPLATE = """
// {% if is_gen_func %}
//   generator function
// {% else %}
//   function
// {% endif %}
// <span class="ml-2 font-family-monospace">
//   {% if lambda_id is none %}
//     {{ name }}
//   {% else %}
//     {{ get_lambda_html(lambda_id) }}
//   {% endif %}
//   (
//   {% for i in range(parameters|length) %}
//     {% set parameter = parameters[i] %}
//     {{ get_parameter_html(parameter) }}
//     {% if i < parameters|length - 1 %}, {% endif %}
//   {% endfor %}
//   )
// </span>
// <div>
//   {{ get_parent_frame_html([parent]) }}
// </div>
// """

// BUILTIN_FUNCTION_TEMPLATE = """
// function
// <span class="ml-2 font-family-monospace">
//   {{ name }}(...)
// </span>
// """

// LAMBDA_TEMPLATE = """
// &#955;
// <sub>
//   {{ lineno }}
//   {% if not single %}
//     #{{ number }}
//   {% endif %}
// </sub>
// """

// ORDERED_COLLECTION_TEMPLATE = """
// {% if elements|length == 0 %}
//   empty {{ type }}
// {% else %}
//   <div class="d-flex flex-row align-items-center">
//     <div>{{type}}</div>
//     <table class="pyagram-ordered-collection border-collapse ml-1 font-family-monospace" rules="cols">
//     <tr>
//       {% for element in elements %}
//         <td class="pyagram-collection-element px-2">{{ get_reference_html(element) }}</td>
//       {% endfor %}
//     </tr>
//   </table>
//   </div>
// {% endif %}
// """

// UNORDERED_COLLECTION_TEMPLATE = """
// {% if elements|length == 0 %}
//   empty {{ type }}
// {% else %}
//   <div class="d-flex flex-row align-items-center">
//     <div>{{type}}</div>
//     <table class="pyagram-unordered-collection ml-1 font-family-monospace">
//     <tr>
//       {% for element in elements %}
//         <td class="pyagram-collection-element px-2">{{ get_reference_html(element) }}</td>
//       {% endfor %}
//     </tr>
//   </table>
//   </div>
// {% endif %}
// """

// MAPPING_TEMPLATE = """
// {% if items|length == 0 %}
//   empty {{ type }}
// {% else %}
//   <div class="d-flex flex-row align-items-center">
//     <div>{{type}}</div>
//     <table class="pyagram-mapping border-collapse ml-1 font-family-monospace" rules="cols">
//     <tr>
//       {% for item in items %}
//         <td class="pyagram-mapping-key px-2 text-center">{{ get_reference_html(item[0]) }}</td>
//       {% endfor %}
//     </tr>
//     <tr>
//       {% for item in items %}
//         <td class="pyagram-mapping-value px-2 text-center">{{ get_reference_html(item[1]) }}</td>
//       {% endfor %}
//     </tr>
//   </table>
//   </div>
// {% endif %}
// """

// ITERATOR_TEMPLATE = """
// {% if object is none %}
//   empty iterator
// {% else %}
//   iterator over <span class="pyagram-value">{{ get_reference_html(object) }}</span>
//   {% if annotation is not none %}
//     <span> {{ annotation }}</span>
//   {% endif %}
//   <div>[next index: {{ index }}]</div>
// {% endif %}
// """

// # TODO: Reconsider how you display these.
// OBJECT_REPR_TEMPLATE = """
// <div class="font-family-monospace">
//   {{ repr }}
// </div>
// """

// PARENT_FRAME_TEMPLATE = """
// {% if parents|length == 0 %}
// {% elif parents|length == 1 %}
//   [parent: {{ parents[0] }}]
// {% else %}
//   [parents: {% for i in range(parents|length - 1) %}{{ parents[i] }}, {% endfor %}{{ parents[-1] }}]
// {% endif %}
// """

// PARAMETER_TEMPLATE = """
// {{ name }}
// {% if default is not none %}
//   =<span class="pyagram-value">{{ get_reference_html(default) }}</span>
// {% endif %}
// """

// PRINT_TEMPLATE = """
// {% for line in print_output %}
//   <div class="print-output {% if is_exception %} pyagram-exception {% endif %} font-family-monospace">
//     {{ line }}
//   </div>
// {% endfor %}
// """