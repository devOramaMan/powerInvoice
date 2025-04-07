import argparse

import pdfplumber

import cv2
import json

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from textwrap import wrap

from InvoiceData import InvoiceTypes



# Load bounding boxes from the JSON file
def load_bounding_boxes():
    json_file = "regions.json"
    with open(json_file, "r") as file:
        data = json.load(file)
        # Extract the "boundaries" from each region
        #bounding_boxes = [tuple(region["boundaries"]) for region in data["regions"]]
        return data["regions"]

helpstr="""
Calculate user usage and cost distribution. 

Example: python ./account_maker_pdf.py [faktura.pdf]
"""

def draw_wrapped_text(c, text, x, y, max_width, font_name="Helvetica", font_size=10, line_spacing=12):
    """
    Draws wrapped text on the canvas.
    """
    c.setFont(font_name, font_size)
    lines = wrap(text, width=max_width // (font_size * 0.6))  # Estimate characters per line
    for line in lines:
        c.drawString(x, y, line)
        y -= line_spacing  # Move to the next line
    return y  # Return the updated y-coordinate

def generate_invoice_pdf(types, user_data):
    filename = "power_invoice_%s.pdf" % str(types.invoice_month_str)
    # Create a canvas for the PDF
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, f"{user_data["heading"]} {user_data['name']}")

    # General Information
    c.setFont("Helvetica", 12)
    gen_info = user_data["gen-info"]
    # Replace placeholders with dynamic data
    gen_info = gen_info.replace("##Address", str(types.street))
    gen_info = gen_info.replace("##usage_tot", str(types.total_usage))
    gen_info = gen_info.replace("##user_usage", str(types.user_usage))
    gen_info = gen_info.replace("##user_percent", f"{types.user_percent:.2f}%")
    gen_info = gen_info.replace("##cost_tot", f"{types.total_cost:.2f}")
    gen_info = gen_info.replace("##user_cost", f"{types.user_cost:.2f}")
    
    y = draw_wrapped_text(c, gen_info, 50, height - 120, max_width=500)
    y = draw_wrapped_text(c, user_data["usage-info"], 50, y - 40, max_width=500)

    # Link
    c.drawString(50, y - 100, "For more details, visit:")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y - 120, user_data["link"])

    # Account Information
    c.setFont("Helvetica", 12)
    c.drawString(50, y - 320, user_data["account"])

    # Save the PDF
    c.save()
    print(f"Invoice generated: {filename}")



    
#main
if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    #print(sys.argv)
    parser = argparse.ArgumentParser(description=helpstr)
    parser.add_argument("--show", "-s", help="Make a image with the bounding boxes", required=False, action="store_true")
    parser.add_argument("--update", "-u", help="Update/adapt the bounding boxes", required=False, action="store_true")
    parser.add_argument("pdf_file", help="Path to the PDF invoice file to process")
    args = parser.parse_args()

    BOUNDING_BOXES = load_bounding_boxes()

    if args.show:
        import selectinwindow

        for idx, bbox in zip(range(len(BOUNDING_BOXES)), BOUNDING_BOXES):
            with pdfplumber.open(args.pdf_file) as pdf:
                page = pdf.pages[bbox.get("page", 0)]
                # Visualize the page layout
                box = bbox['boundaries']
                im = page.to_image()
                name = bbox.get('name', "page_image_box%d" % idx)
                im.draw_rect(box)  # Draw the bounding box
                
                im.save('%s.png' % (name))
                # Extract text from the bounding box
                text = page.within_bbox(box).extract_text()
                print(f"Extracted text from bbox {name} {box}:\n{text}")

        if args.update:

            update_cnt = 0
            for idx, bbox in zip(range(len(BOUNDING_BOXES)), BOUNDING_BOXES):
                # Load the image saved from pdfplumber
                fname = bbox.get('name', "page_image_box%d" % idx)
                wName = '%s.png (double click the rectangle to update the boundaries)' % fname

                image = cv2.imread(fname+".png")
                #get the width and height of the image
                imageHeight, imageWidth = image.shape[:2]

                rectI = selectinwindow.DragRectangle(image, wName, imageWidth, imageHeight)
                cv2.namedWindow(rectI.wname)
                cv2.setMouseCallback(rectI.wname, selectinwindow.dragrect, rectI)

                # keep looping until rectangle finalized
                if selectinwindow.run(rectI) is True:
                    print("Updated coordinates")
                    x1, y1, x2, y2 = rectI.outRect.x, rectI.outRect.y, rectI.outRect.x + rectI.outRect.w, rectI.outRect.y + rectI.outRect.h
                    bbox['boundaries'] = (x1, y1, x2, y2)
                    update_cnt += 1
                    print(str(BOUNDING_BOXES[idx]))

            # Save the updated bounding boxes to the JSON file
            if update_cnt > 0:
                json_file = "regions.json"
                with open(json_file, "r") as file:
                    data = json.load(file)
                    for idx, bbox in zip(range(len(BOUNDING_BOXES)), BOUNDING_BOXES):
                        data["regions"][idx]["boundaries"] = list(bbox['boundaries'])
                with open(json_file, "w") as file:    
                    json.dump(data, file, indent=4)
                print(f"Updated bounding boxes saved to {json_file}")
            
        exit(0)

    print(f"Processing {args.pdf_file}")
    
    # Extract text from PDF
    
    with pdfplumber.open(args.pdf_file) as pdf:
        if len(pdf.pages) < 2:
            raise ValueError("Missing pages in the PDF file (pages %s) " % (str(len(pages))))
        for bbox in BOUNDING_BOXES:
            pagenum = bbox.get("page", 0)
            if pagenum >= len(pdf.pages):
                raise ValueError("Page number %d is out of range" % pagenum)
            page = pdf.pages[pagenum]
            box = bbox["boundaries"]
            text = page.within_bbox(box).extract_text()
            bbox['extract'] = (text)


        

    types = InvoiceTypes()
    types.parse(BOUNDING_BOXES)
    #Get user usage from server. test with 600 khw usage:
    user_usage = 600
    types.calculate_user_data(user_usage)

    with open("user.json", "r", encoding="utf-8" ) as file:
        user_data = json.load(file)

        generate_invoice_pdf(types, user_data)

    print(f"Name: {types.street}")
    print(f"Total usage: {types.total_usage} {types.USAGE}")
    print(f"User usage: {types.user_usage} {types.USAGE}")
    print(f"User percent: {types.user_percent:.2f}%")










    

# Retrieve Faktura Name and address


