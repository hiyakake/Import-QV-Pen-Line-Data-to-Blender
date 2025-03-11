# QV ペンで描いた絵を Blender に読み込むやつ / Import QV-Pen Line Data to Blender

## 概要

### 日本語

このプラグインは QV-Pen のデータを Blender にインポートするためのものです。

QV ペンのデータを Dolphiiiin 様作成の「QvPen Exporter / Importer」（https://booth.pm/ja/items/6499949）が設置されたワールドでエクスポートし、「QvPen Export Formatter」（https://dolphiiiin.github.io/qvpen-export-formatter/）を使ってJSONファイルに変換したものを本ツールに読み込ませるとメッシュ化したパスとしてインポートできます。

色と太さが引き継がれます。

座標は、VRC のワールド上で描かれた場所と対応します。

### English

This plugin imports QV-Pen line data to Blender. Export QV-Pen data from the world where Dolphiiiin's "QvPen Exporter / Importer" (https://booth.pm/ja/items/6499949) is installed, and use "QvPen Export Formatter" (https://dolphiiiin.github.io/qvpen-export-formatter/) to convert it into a JSON file. This tool can import the converted JSON file as a mesh path. The color and thickness are inherited. The coordinates correspond to the location where the line is drawn on the VRC world.

## 使い方

### 日本語

- インストールすると N パネルに「QV Pen」という名のパネルができるので、そこを開いてください。
- パネルの中には「Select JSON File」というボタンがあるので、それを押して前述のツールで作成した JSON ファイルを選択してください。
- 基本的にはワールドに設置されている QV Pen の太さ情報を読み込みます。太さが未定義の場合はこの入力欄に設定した太さが適用されます。
- 「Add Solidify Modifier」にチェックを入れると、太さに応じてソリッド化モディファイアが追加されます。メッシュ化したい場合はこれを有効にしてください。
- 「Generate Paths」を押すと、パスもしくはソリッド化したメッシュが生成されます。

### English

- After installing, a panel named "QV Pen" will be created in the N panel. Open it.
- There is a button called "Select JSON File" in the panel. Click it to select the JSON file created by the above tool.
  - The default extrude value can be changed to override it uniformly.
- If "Add Solidify Modifier" is checked, a solidify modifier will be added according to the thickness. If you want to mesh, please enable it.
- Click "Generate Paths" to generate a path or a solidified mesh.

## 注意点

### 日本語

- 座標は VRC のワールド上で描かれた場所と対応します。

### English

- The coordinates correspond to the location where the line is drawn on the VRC world.
