from utils.helperFunctions import *
import shutil
gr.close_all()

def export_to_excel(origin, df):
	path = f"distance matrix {origin}.xlsx"
	df.to_excel(path,index = False)
	return path

def download_template():
    new_file_path = "destination_template.xlsx"
    shutil.copyfile("input/input_clean.xlsx", new_file_path)
    return new_file_path

df = gr.Dataframe(placeholder_df, render=False)

with gr.Blocks(css="footer{display:none !important}") as app:
	with gr.Tab(label="Time and Distance Matrix"):
		welcome_1 = gr.Markdown(
			value = "# Welcome to the Time and Distance Matrix app"
		)
		intro = gr.Markdown(
			value = '''This app let you compute the time and distance matrix from an origin to a prefilled list of destination.
					
			After computing the matrix, you can download the results by double-clicking the `Download` button.'''
		)
		with gr.Blocks():
			origin = gr.Textbox(
				placeholder="Färbergraben 16, München",
				value="Färbergraben 16, München",
				label="Origin",
				info = "Enter the starting point to compute here"
			)
			with gr.Row():
				with gr.Column(scale=4):
					compute_btn = gr.Button(value="Submit")
				with gr.Column(scale=4):
					clear_btn = gr.ClearButton([origin])
				with gr.Column(scale=4):
					download_results_btn = gr.DownloadButton()

		with gr.Blocks():
			gr.Markdown(value="## Time and Distance Matrix")
		df.render()

	with gr.Tab(label="Manage Destinations"):
		welcome_2 = gr.Markdown(
			value = "# Manage Destinations"
		)
		intro = gr.Markdown(
			value = '''
			Here, you can manage the destinations that would be used to compute the time and distance matrix.
			
			If you want to upload a new file, you can click on `Clear` and download the file.
			
			If you want to download the template, just click on the small link on the bottom right of the window. If the file is not visible, click on `Reset`.
			'''
		)

		with gr.Column():
			file_component = gr.File(
				label="Download/Upload",
				value="input/input_clean.xlsx",
				min_width = 300,
				scale=1
			)
			gr.Textbox(scale=3, visible=False)
		with gr.Row():
			reset_file_component = gr.Button("Reset")
			clear_file_component = gr.ClearButton(file_component)
################################################## EVENT LISTENERS ##################################################
		compute_btn.click(
			fn = compute_and_display_travel_times_and_distances,
			inputs = [origin, file_component],
			outputs = [df]
		)
		download_results_btn.click(
			fn=export_to_excel,
			inputs=[origin, df],
			outputs=[download_results_btn]
		)	
		reset_file_component.click(
			fn=lambda x:"input/input_clean.xlsx",
			outputs=file_component
		)

gr.close_all()
app.launch()
