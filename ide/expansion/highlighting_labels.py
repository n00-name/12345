from pygments.token import Token

labels = {
    Token: 'For any kind of token (especially if it doesn’t match any of the subtypes of course).',
    Token.Escape: 'For any escape',
    Token.Text: 'For any type of text data',
    Token.Text.Whitespace: 'For whitespace',
    Token.Error: 'represents lexer errors',
    Token.Other: 'special token for data not matched by a parser (e.g. HTML markup in PHP code)',
    Token.Keyword: 'For any kind of keyword '
                   '(especially if it doesn’t match any of the subtypes of course).',
    Token.Keyword.Constant: 'For keywords that are constants (e.g. None in future Python versions).',
    Token.Keyword.Declaration: 'For keywords used for variable declaration '
                               '(e.g. var in some programming languages'
                               'like JavaScript).',
    Token.Keyword.Namespace: 'For keywords used for namespace declarations '
                             '(e.g. import in Python and Java and '
                             'package in Java).',
    Token.Keyword.Pseudo: 'For keywords that aren’t really keywords '
                          '(e.g. None in old Python versions).',
    Token.Keyword.Reserved: 'For reserved keywords.',
    Token.Keyword.Type: 'For builtin types that can not be used as identifiers (e.g. int, char etc. in C).',
    Token.Name: 'For any name (variable names, function names, classes).',
    Token.Name.Attribute: 'For all attributes (e.g. in HTML tags).',
    Token.Name.Builtin: 'Builtin names; names that are available in the global namespace.',
    Token.Name.Builtin.Pseudo: 'Builtin names that are implicit (e.g. self in Ruby, this in Java).',
    Token.Name.Class: 'Class names. '
                      'Because no lexer can know if a name is a class or a function or something '
                      'else this token is meant for class declarations.',
    Token.Name.Constant: 'Token type for constants. '
                         'In some languages you can recognise a token by the way '
                         'it’s defined (the value after a const keyword for example). In other languages '
                         'constants are uppercase by definition (Ruby).',
    Token.Name.Decorator: 'Token type for decorators. '
                          'Decorators are syntactic elements in the Python '
                          'language. Similar syntax elements exist in C# and Java.',
    Token.Name.Entity: 'Token type for special entities. (e.g. &nbsp; in HTML).',
    Token.Name.Exception: 'Token type for exception names (e.g. RuntimeError in Python). '
                          'Some languages '
                          'define exceptions in the function signature (Java). '
                          'You can highlight the name of that '
                          'exception using this token then.',
    Token.Name.Function: 'Token type for function names.',
    Token.Name.Function.Magic: 'same as Name.Function but for '
                               'special function names that have an implicit '
                               'use in a language (e.g. __init__ method in Python).',
    Token.Name.Label: 'Token type for label names (e.g. in languages that support goto).',
    Token.Name.Namespace: 'Token type for namespaces. '
                          '(e.g. import paths in Java/Python), names following '
                          'the module/namespace keyword in other languages.',
    Token.Name.Other: 'Other names. Normally unused.',
    Token.Name.Property: 'Additional token type occasionally used for class attributes.',
    Token.Name.Tag: 'Tag names (in HTML/XML markup or configuration files).',
    Token.Name.Variable: 'Token type for variables. '
                         'Some languages have prefixes for variable names '
                         '(PHP, Ruby, Perl). You can highlight them using this token.',
    Token.Name.Variable.Class: 'same as Name.Variable '
                               'but for class variables (also static variables).',
    Token.Name.Variable.Global: 'same as Name.Variable '
                                'but for global variables (used in Ruby, for example).',
    Token.Name.Variable.Instance: 'same as Name.Variable but for instance variables.',
    Token.Name.Variable.Magic: 'same as Name.'
                               'Variable but for special variable names that have an implicit '
                               'use in a language (e.g. __doc__ in Python).',
    Token.Literal: 'For any literal (if not further defined).',
    Token.Literal.Date: 'for date literals (e.g. 42d in Boo).',
    Token.String: 'For any string literal.',
    Token.String.Affix:
        'Token type for affixes that further specify '
        'the type of the string they’re attached '
                        'to (e.g. the prefixes r and u8 in r"foo" and u8"foo").',
    Token.String.Backtick: 'Token type for strings enclosed in backticks.',
    Token.String.Char: 'Token type for single characters (e.g. Java, C).',
    Token.String.Delimiter:
        "Token type for delimiting identifiers in “heredoc”, raw and other similar "
                            "strings (e.g. the word END in Perl code print <<'END';).",
    Token.String.Doc: 'Token type for documentation strings (for example Python).',
    Token.String.Double: 'Double quoted strings.',
    Token.String.Escape: 'Token type for escape sequences in strings.',
    Token.String.Heredoc: 'Token type for “heredoc” strings (e.g. in Ruby or Perl).',
    Token.String.Interpol: 'Token type for interpolated parts in strings (e.g. #{foo} in Ruby).',
    Token.String.Other:
        'Token type for any other strings (for example %q{foo} string constructs in Ruby).',
    Token.String.Regex: 'Token type for regular expression literals (e.g. /foo/ in JavaScript).',
    Token.String.Single: 'Token type for single quoted strings.',
    Token.String.Symbol: 'Token type for symbols (e.g. :foo in LISP or Ruby).',
    Token.Number: 'Token type for any number literal.',
    Token.Number.Bin: 'Token type for binary literals (e.g. 0b101010).',
    Token.Number.Float: 'Token type for float literals (e.g. 42.0).',
    Token.Number.Hex: 'Token type for hexadecimal number literals (e.g. 0xdeadbeef).',
    Token.Number.Integer: 'Token type for integer literals (e.g. 42).',
    Token.Number.Integer.Long: 'Token type for long integer literals (e.g. 42L in Python).',
    Token.Number.Oct: 'Token type for octal literals.',
    Token.Operator: 'For any punctuation operator (e.g. +, -).',
    Token.Operator.Word: 'For any operator that is a word (e.g. not).',
    Token.Punctuation:
        'For any punctuation which is not an operator (e.g. [, (…)',
    Token.Punctuation.Marker:
        'For markers that point to a location '
        '(e.g., carets in Python tracebacks for syntax errors).',
    Token.Comment: 'Token type for any comment.',
    Token.Comment.Hashbang:
        'Token type for hashbang comments (i.e. first lines of files that start with #!).',
    Token.Comment.Multiline: 'Token type for multiline comments.',
    Token.Comment.Preproc: 'Token type for preprocessor comments (also <?php/<% constructs).',
    Token.Comment.PreprocFile:
        'Token type for filenames in preprocessor comments, such as include files in C/C++.',
    Token.Comment.Single: 'Token type for comments that end at the end of a line (e.g. # foo).',
    Token.Comment.Special:
        'Special data in comments. For example code tags, author and license information, etc.',
    Token.Generic: 'A generic, unstyled token. Normally you don’t use this token type.',
    Token.Generic.Deleted: 'Marks the token value as deleted.',
    Token.Generic.Emph: 'Marks the token value as emphasized.',
    Token.Generic.Error: 'Marks the token value as an error message.',
    Token.Generic.Heading: 'Marks the token value as headline.',
    Token.Generic.Inserted: 'Marks the token value as inserted.',
    Token.Generic.Output: 'Marks the token value as program output (e.g. for python cli lexer).',
    Token.Generic.Prompt: 'Marks the token value as command prompt (e.g. bash lexer).',
    Token.Generic.Strong: 'Marks the token value as bold (e.g. for rst lexer).',
    Token.Generic.Subheading: 'Marks the token value as subheadline.',
    Token.Generic.Traceback: 'Marks the token value as a part of an error traceback.'
}
