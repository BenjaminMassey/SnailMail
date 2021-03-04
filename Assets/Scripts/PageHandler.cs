using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class PageHandler : MonoBehaviour
{
    public int page;

    private GameObject[] buttons;
    private int real_button_num;

    private GameObject up_button;
    private GameObject down_button;

    private Color def_color;

    // Start is called before the first frame update
    void Start()
    {
        page = 0;
        buttons = new GameObject[10];
        for (int i = 0; i < 10; i++)
        {
            buttons[i] = GameObject.Find("Level" + (i + 1).ToString() + " Button");
        }
        def_color = buttons[0].GetComponent<Button>().colors.normalColor;

        up_button = GameObject.Find("Up Button");
        down_button = GameObject.Find("Down Button");

        UpdateNavButtons();
    }

    public void PageDown()
    {
        page++;
        page = Mathf.Min(Unlocks.num_levels / 10, page);
        //Debug.Log("MAX PAGES: " + Unlocks.num_levels / 10);
        UpdatePage();
        UpdateNavButtons();
    }

    public void PageUp()
    {
        page--;
        page = Mathf.Max(0, page);
        UpdatePage();
        UpdateNavButtons();
    }

    void UpdatePage()
    {
        for (int rel_num = 0; rel_num < 10; rel_num++)
        {
            int num = (page * 10) + rel_num;
            if (num < Unlocks.num_levels)
            {
                NewButton(num);
            }
            else
            {
                //Debug.Log("REL NUM: " + rel_num);
                buttons[rel_num].name = "Non-Button";
                buttons[rel_num].GetComponent<Image>().enabled = false;
                buttons[rel_num].GetComponent<Button>().enabled = false;
                buttons[rel_num].transform.GetChild(0).GetComponent<Text>().enabled = false;
            }
        }
        GameObject.Find("Canvas").GetComponent<Unlocker>().UpdateButtons();
    }

    void NewButton(int num)
    {
        int rel_num = num % 10;
        string str_num = (num + 1).ToString();
        buttons[rel_num].name = "Level" + str_num + " Button";
        buttons[rel_num].transform.GetChild(0).GetComponent<Text>().text = "Level " + str_num;

        ColorBlock cb = buttons[rel_num].GetComponent<Button>().colors;
        if (num > 12) // Moon Levels Color
        {
            cb.normalColor = new Color(0.4f, 0, 0.4f);
            buttons[rel_num].transform.GetChild(0).GetComponent<Text>().color = new Color(1, 1, 1);
        }
        else
        {
            cb.normalColor = def_color;
            buttons[rel_num].transform.GetChild(0).GetComponent<Text>().color = new Color(0, 0, 0);
        }
        buttons[rel_num].GetComponent<Button>().colors = cb;

        buttons[rel_num].GetComponent<Image>().enabled = true;
        buttons[rel_num].GetComponent<Button>().enabled = true;
        buttons[rel_num].transform.GetChild(0).GetComponent<Text>().enabled = true;
    }

    void UpdateNavButtons()
    {
        if (page == 0)
        {
            up_button.SetActive(false);
        }
        else
        {
            up_button.SetActive(true);
        }

        if (page == (Unlocks.num_levels / 10) || Unlocks.num_levels <= 10)
        {
            down_button.SetActive(false);
        }
        else
        {
            down_button.SetActive(true);
        }
    }
}
